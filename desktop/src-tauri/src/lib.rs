use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    fs,
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::Mutex,
    time::{Duration, Instant},
};
use tauri::{AppHandle, Emitter, Manager, RunEvent, State, WindowEvent};

#[cfg(unix)]
use std::os::unix::process::CommandExt;
#[cfg(target_os = "macos")]
use tauri::menu::{Menu, MenuItemBuilder, MenuItemKind, PredefinedMenuItem};

const DEFAULT_PORT: u16 = 31527;
const DEFAULT_REFRESH_INTERVAL_MINUTES: u16 = 60;
const OPEN_FEED_EVENT: &str = "open-feed";
const REFRESH_FEED_EVENT: &str = "refresh-feed";
const OPEN_SEARCH_EVENT: &str = "open-search";
const OPEN_SETTINGS_EVENT: &str = "open-settings";
const FEED_MENU_ID: &str = "feed";
const REFRESH_MENU_ID: &str = "refresh-feed";
const SEARCH_MENU_ID: &str = "search";
const SETTINGS_MENU_ID: &str = "settings";

#[derive(Default)]
struct SidecarManager {
    child: Mutex<Option<Child>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct DesktopConfig {
    server_port: u16,
    feed_refresh_interval_minutes: u16,
    api_base_url: String,
    config_path: String,
    db_path: String,
    log_dir: String,
}

#[derive(Debug, Serialize)]
struct SidecarStatus {
    ready: bool,
    port: u16,
    message: String,
}

#[tauri::command]
fn get_config() -> Result<DesktopConfig, String> {
    read_or_init_config()
}

#[tauri::command]
fn check_port_available(port: u16) -> bool {
    is_port_available(port)
}

#[tauri::command]
fn sidecar_health(port: u16) -> SidecarStatus {
    let ready = health_check(port);
    SidecarStatus {
        ready,
        port,
        message: if ready {
            "local service is ready".to_string()
        } else {
            "local service is not reachable".to_string()
        },
    }
}

#[tauri::command]
fn start_sidecar(
    app: AppHandle,
    manager: State<'_, SidecarManager>,
) -> Result<SidecarStatus, String> {
    let config = read_or_init_config()?;
    let port = config.server_port;

    if health_check(port) {
        return Ok(SidecarStatus {
            ready: true,
            port,
            message: "local service is already running".to_string(),
        });
    }

    if !ensure_port_available(&app, port) {
        return Err(format!(
            "port {port} is already in use and does not respond as NBER-CLI Desktop"
        ));
    }

    let mut child = spawn_sidecar(&app, &config)?;
    if wait_for_health(port, Duration::from_secs(10)) {
        let mut slot = manager
            .child
            .lock()
            .map_err(|_| "failed to lock sidecar state".to_string())?;
        *slot = Some(child);
        return Ok(SidecarStatus {
            ready: true,
            port,
            message: "local service started".to_string(),
        });
    }

    let _ = child.kill();
    let _ = child.wait();
    Err("local service did not become ready within 10 seconds".to_string())
}

#[tauri::command]
fn stop_sidecar(manager: State<'_, SidecarManager>) -> Result<SidecarStatus, String> {
    kill_sidecar(manager.inner())?;
    let config = read_or_init_config()?;
    Ok(SidecarStatus {
        ready: false,
        port: config.server_port,
        message: "local service stopped".to_string(),
    })
}

fn read_or_init_config() -> Result<DesktopConfig, String> {
    let home = nber_home_dir()?;
    let app_dir = home.join(".nber-cli");
    let config_path = app_dir.join("config.json");
    let db_path = app_dir.join("nber.db");
    let log_dir = app_dir.join("logs");
    fs::create_dir_all(&app_dir).map_err(|error| error.to_string())?;
    fs::create_dir_all(&log_dir).map_err(|error| error.to_string())?;

    let mut config = if config_path.exists() {
        let text = fs::read_to_string(&config_path).map_err(|error| error.to_string())?;
        serde_json::from_str::<Value>(&text).unwrap_or_else(|_| json!({}))
    } else {
        json!({})
    };

    let desktop = config
        .as_object_mut()
        .ok_or_else(|| "config root must be an object".to_string())?
        .entry("desktop")
        .or_insert_with(|| json!({}));
    let desktop_obj = desktop
        .as_object_mut()
        .ok_or_else(|| "desktop config must be an object".to_string())?;

    let server_port = desktop_obj
        .get("server_port")
        .and_then(|value| value.as_u64())
        .filter(|value| (1024..=65535).contains(value))
        .map(|value| value as u16)
        .unwrap_or(DEFAULT_PORT);
    let refresh_interval = desktop_obj
        .get("feed_refresh_interval_minutes")
        .and_then(|value| value.as_u64())
        .filter(|value| *value > 0 && *value <= u16::MAX as u64)
        .map(|value| value as u16)
        .unwrap_or(DEFAULT_REFRESH_INTERVAL_MINUTES);

    desktop_obj.insert("server_port".to_string(), json!(server_port));
    desktop_obj.insert(
        "feed_refresh_interval_minutes".to_string(),
        json!(refresh_interval),
    );
    fs::write(
        &config_path,
        serde_json::to_string_pretty(&config).map_err(|error| error.to_string())? + "\n",
    )
    .map_err(|error| error.to_string())?;

    Ok(DesktopConfig {
        server_port,
        feed_refresh_interval_minutes: refresh_interval,
        api_base_url: format!("http://127.0.0.1:{server_port}/api/v1"),
        config_path: config_path.to_string_lossy().to_string(),
        db_path: db_path.to_string_lossy().to_string(),
        log_dir: log_dir.to_string_lossy().to_string(),
    })
}

fn nber_home_dir() -> Result<PathBuf, String> {
    if let Ok(home) = std::env::var("HOME") {
        return Ok(PathBuf::from(home));
    }
    if let Ok(profile) = std::env::var("USERPROFILE") {
        return Ok(PathBuf::from(profile));
    }
    Err("could not determine user home directory".to_string())
}

fn spawn_sidecar(app: &AppHandle, config: &DesktopConfig) -> Result<Child, String> {
    if cfg!(debug_assertions) {
        let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        let repo_root = manifest_dir
            .parent()
            .and_then(|desktop_dir| desktop_dir.parent())
            .ok_or_else(|| "failed to locate repository root".to_string())?
            .to_path_buf();
        let (stdout_log, stderr_log) = sidecar_stdio(config)?;
        let mut command = Command::new("uv");
        command
            .args([
                "run",
                "nber-sidecar",
                "--host",
                "127.0.0.1",
                "--port",
                &config.server_port.to_string(),
                "--db-path",
                &config.db_path,
                "--log-dir",
                &config.log_dir,
            ])
            .current_dir(repo_root)
            .stdin(Stdio::null())
            .stdout(stdout_log)
            .stderr(stderr_log);
        configure_sidecar_process(&mut command);
        return command
            .spawn()
            .map_err(|error| format!("failed to start development sidecar: {error}"));
    }

    let sidecar_path = production_sidecar_path(app)?;
    let (stdout_log, stderr_log) = sidecar_stdio(config)?;
    let mut command = Command::new(sidecar_path);
    command
        .args([
            "--host",
            "127.0.0.1",
            "--port",
            &config.server_port.to_string(),
            "--db-path",
            &config.db_path,
            "--log-dir",
            &config.log_dir,
        ])
        .stdin(Stdio::null())
        .stdout(stdout_log)
        .stderr(stderr_log);
    configure_sidecar_process(&mut command);
    command
        .spawn()
        .map_err(|error| format!("failed to start bundled sidecar: {error}"))
}

#[cfg(unix)]
fn configure_sidecar_process(command: &mut Command) {
    command.process_group(0);
}

#[cfg(not(unix))]
fn configure_sidecar_process(_command: &mut Command) {}

fn sidecar_stdio(config: &DesktopConfig) -> Result<(Stdio, Stdio), String> {
    let log_dir = PathBuf::from(&config.log_dir);
    fs::create_dir_all(&log_dir).map_err(|error| error.to_string())?;

    let stdout = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(log_dir.join("sidecar.stdout.log"))
        .map_err(|error| format!("failed to open sidecar stdout log: {error}"))?;
    let stderr = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(log_dir.join("sidecar.stderr.log"))
        .map_err(|error| format!("failed to open sidecar stderr log: {error}"))?;

    Ok((Stdio::from(stdout), Stdio::from(stderr)))
}

fn production_sidecar_path(app: &AppHandle) -> Result<PathBuf, String> {
    if let Ok(path) = std::env::var("NBER_SIDECAR_PATH") {
        return Ok(PathBuf::from(path));
    }

    let file_name = if cfg!(windows) {
        "nber-sidecar.exe"
    } else {
        "nber-sidecar"
    };

    let mut candidates = Vec::new();
    if let Ok(resource_dir) = app.path().resource_dir() {
        candidates.push(resource_dir.join(file_name));
        candidates.push(resource_dir.join("binaries").join(file_name));
    }
    if let Ok(current_exe) = std::env::current_exe() {
        if let Some(parent) = current_exe.parent() {
            candidates.push(parent.join(file_name));
            candidates.push(parent.join("../Resources").join(file_name));
        }
    }

    candidates
        .into_iter()
        .find(|path| path.exists())
        .ok_or_else(|| "bundled sidecar executable was not found".to_string())
}

fn is_port_available(port: u16) -> bool {
    TcpListener::bind(("127.0.0.1", port)).is_ok()
}

fn ensure_port_available(app: &AppHandle, port: u16) -> bool {
    if is_port_available(port) {
        return true;
    }
    cleanup_residual_sidecar(app);
    wait_for_port_release(port, Duration::from_secs(3))
}

fn wait_for_port_release(port: u16, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if is_port_available(port) {
            return true;
        }
        std::thread::sleep(Duration::from_millis(250));
    }
    false
}

fn cleanup_residual_sidecar(app: &AppHandle) {
    if let Ok(path) = production_sidecar_path(app) {
        terminate_processes_with_executable(&path);
    }
}

fn terminate_processes_with_executable(path: &PathBuf) {
    if cfg!(windows) {
        terminate_windows_processes(path);
    } else {
        terminate_unix_processes(path);
    }
}

fn terminate_unix_processes(path: &PathBuf) {
    let path_text = path.to_string_lossy().to_string();
    let Ok(output) = Command::new("ps").args(["-axo", "pid=,command="]).output() else {
        return;
    };
    let current_pid = std::process::id();
    for line in String::from_utf8_lossy(&output.stdout).lines() {
        let Some((pid_text, command)) = line.trim().split_once(' ') else {
            continue;
        };
        let Ok(pid) = pid_text.trim().parse::<u32>() else {
            continue;
        };
        if pid == current_pid || !command.contains(&path_text) {
            continue;
        }
        let _ = Command::new("kill")
            .args(["-TERM", &pid.to_string()])
            .status();
    }
}

fn terminate_windows_processes(path: &PathBuf) {
    let path_text = path.to_string_lossy().replace('\'', "''");
    let script = format!(
        "$target = [IO.Path]::GetFullPath('{path_text}'); \
         Get-CimInstance Win32_Process | \
         Where-Object {{ $_.ExecutablePath -and ([IO.Path]::GetFullPath($_.ExecutablePath) -eq $target) }} | \
         ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"
    );
    let _ = Command::new("powershell")
        .args(["-NoProfile", "-Command", &script])
        .status();
}

fn wait_for_health(port: u16, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if health_check(port) {
            return true;
        }
        std::thread::sleep(Duration::from_millis(250));
    }
    false
}

fn health_check(port: u16) -> bool {
    let Ok(mut stream) = TcpStream::connect(("127.0.0.1", port)) else {
        return false;
    };
    let _ = stream.set_read_timeout(Some(Duration::from_secs(1)));
    let request = "GET /api/v1/health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n";
    if stream.write_all(request.as_bytes()).is_err() {
        return false;
    }
    let mut response = String::new();
    if stream.read_to_string(&mut response).is_err() {
        return false;
    }
    response.contains("200 OK") && response.contains("\"status\":\"ok\"")
}

fn kill_sidecar(manager: &SidecarManager) -> Result<(), String> {
    let mut slot = manager
        .child
        .lock()
        .map_err(|_| "failed to lock sidecar state".to_string())?;
    if let Some(mut child) = slot.take() {
        terminate_sidecar_process(&mut child);
    }
    Ok(())
}

fn terminate_sidecar_process(child: &mut Child) {
    #[cfg(unix)]
    {
        let process_group = format!("-{}", child.id());
        let _ = Command::new("kill")
            .args(["-TERM", &process_group])
            .status();
        let deadline = Instant::now() + Duration::from_secs(2);
        while Instant::now() < deadline {
            match child.try_wait() {
                Ok(Some(_)) | Err(_) => return,
                Ok(None) => std::thread::sleep(Duration::from_millis(50)),
            }
        }
        let _ = Command::new("kill")
            .args(["-KILL", &process_group])
            .status();
    }

    #[cfg(not(unix))]
    let _ = child.kill();

    let _ = child.wait();
}

#[cfg(target_os = "macos")]
fn build_macos_menu(app: &AppHandle) -> tauri::Result<Menu<tauri::Wry>> {
    let menu = Menu::default(app)?;
    if let Some(MenuItemKind::Submenu(app_menu)) = menu.items()?.into_iter().next() {
        let settings_item = MenuItemBuilder::with_id(SETTINGS_MENU_ID, "设置…")
            .accelerator("CmdOrCtrl+,")
            .build(app)?;
        let separator = PredefinedMenuItem::separator(app)?;
        app_menu.insert_items(&[&settings_item, &separator], 2)?;
    }

    for item in menu.items()? {
        if let MenuItemKind::Submenu(submenu) = item {
            let submenu_text = submenu.text()?;
            if submenu_text == "Edit" {
                let separator = PredefinedMenuItem::separator(app)?;
                let search_item = MenuItemBuilder::with_id(SEARCH_MENU_ID, "查找…")
                    .accelerator("CmdOrCtrl+F")
                    .build(app)?;
                submenu.append_items(&[&separator, &search_item])?;
            } else if submenu_text == "View" {
                let separator = PredefinedMenuItem::separator(app)?;
                let feed_item = MenuItemBuilder::with_id(FEED_MENU_ID, "论文流")
                    .accelerator("CmdOrCtrl+1")
                    .build(app)?;
                let refresh_item = MenuItemBuilder::with_id(REFRESH_MENU_ID, "同步最新论文")
                    .accelerator("CmdOrCtrl+R")
                    .build(app)?;
                submenu.append_items(&[&separator, &feed_item, &refresh_item])?;
            }
        }
    }

    Ok(menu)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_opener::init())
        .manage(SidecarManager::default())
        .invoke_handler(tauri::generate_handler![
            get_config,
            check_port_available,
            sidecar_health,
            start_sidecar,
            stop_sidecar
        ]);

    #[cfg(target_os = "macos")]
    let builder = builder.menu(build_macos_menu);

    let app = builder
        .on_menu_event(|app, event| match event.id().as_ref() {
            FEED_MENU_ID => {
                let _ = app.emit(OPEN_FEED_EVENT, ());
            }
            SEARCH_MENU_ID => {
                let _ = app.emit(OPEN_SEARCH_EVENT, ());
            }
            REFRESH_MENU_ID => {
                let _ = app.emit(REFRESH_FEED_EVENT, ());
            }
            SETTINGS_MENU_ID => {
                let _ = app.emit(OPEN_SETTINGS_EVENT, ());
            }
            _ => {}
        })
        .on_window_event(|window, event| {
            if matches!(event, WindowEvent::CloseRequested { .. }) {
                let manager = window.state::<SidecarManager>();
                let _ = kill_sidecar(manager.inner());
            }
        })
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri application");

    app.run(|app_handle, event| {
        if matches!(event, RunEvent::ExitRequested { .. } | RunEvent::Exit) {
            let manager = app_handle.state::<SidecarManager>();
            let _ = kill_sidecar(manager.inner());
        }
    });
}
