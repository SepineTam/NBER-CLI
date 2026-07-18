mod commands;
mod config;
mod database;
mod models;
mod worker;

use tauri::{Emitter, Manager};

#[cfg(target_os = "macos")]
use tauri::AppHandle;

#[cfg(target_os = "macos")]
use tauri::menu::{Menu, MenuItemBuilder, MenuItemKind, PredefinedMenuItem};

const OPEN_FEED_EVENT: &str = "open-feed";
const REFRESH_FEED_EVENT: &str = "refresh-feed";
const OPEN_SEARCH_EVENT: &str = "open-search";
const OPEN_SETTINGS_EVENT: &str = "open-settings";
const FEED_MENU_ID: &str = "feed";
const REFRESH_MENU_ID: &str = "refresh-feed";
const SEARCH_MENU_ID: &str = "search";
const SETTINGS_MENU_ID: &str = "settings";

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
    if std::env::var_os("NBER_DESKTOP_INIT_ONLY").is_some() {
        commands::initialize_runtime(None).expect("failed to initialize Desktop data runtime");
        return;
    }

    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            commands::get_config,
            commands::get_feed,
            commands::refresh_feed,
            commands::get_paper,
            commands::set_paper_read_status,
            commands::add_paper_tag,
            commands::rename_paper_tag,
            commands::remove_paper_tag,
            commands::get_settings,
            commands::save_settings,
        ]);

    #[cfg(target_os = "macos")]
    let builder = builder.menu(build_macos_menu);

    builder
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
        .setup(|app| {
            commands::initialize_runtime(Some(app.handle())).map_err(std::io::Error::other)?;
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Tauri application");
}
