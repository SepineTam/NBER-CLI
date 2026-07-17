use crate::models::{FeedSourceItem, PaperMetadata};
use quick_xml::de::from_str;
use regex::Regex;
use serde::Deserialize;
use std::time::Duration;

pub const NBER_FEED_URL: &str = "https://www.nber.org/rss/new.xml";
const USER_AGENT: &str = "curl/8.7.1";

#[derive(Debug, Deserialize)]
struct Rss {
    channel: Channel,
}

#[derive(Debug, Deserialize)]
struct Channel {
    #[serde(rename = "item", default)]
    items: Vec<RssItem>,
}

#[derive(Debug, Deserialize)]
struct RssItem {
    title: Option<String>,
    link: Option<String>,
    guid: Option<String>,
    description: Option<String>,
}

pub async fn download_text(url: &str) -> Result<String, String> {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .http1_only()
        .user_agent(USER_AGENT)
        .build()
        .map_err(display_error)?;
    let mut last_error = String::new();
    for attempt in 0..3 {
        match client
            .get(url)
            .header("Accept", "application/xml,text/html;q=0.9,*/*;q=0.8")
            .send()
            .await
        {
            Ok(response) if response.status().is_success() => match response.text().await {
                Ok(text) => return Ok(text),
                Err(error) => last_error = format!("failed to read {url}: {error}"),
            },
            Ok(response)
                if response.status().is_server_error()
                    || response.status() == reqwest::StatusCode::REQUEST_TIMEOUT =>
            {
                last_error = format!("failed to fetch {url}: HTTP {}", response.status());
            }
            Ok(response) => {
                return Err(format!("failed to fetch {url}: HTTP {}", response.status()));
            }
            Err(error) => last_error = format!("failed to fetch {url}: {error}"),
        }
        if attempt < 2 {
            tokio::time::sleep(Duration::from_secs(1 << attempt)).await;
        }
    }
    Err(last_error)
}

pub fn parse_feed(xml_text: &str) -> Result<Vec<FeedSourceItem>, String> {
    let repaired = repair_feed_xml(xml_text);
    let rss: Rss = from_str(&repaired).map_err(|error| format!("invalid NBER RSS XML: {error}"))?;
    let paper_id_pattern = Regex::new(r"/papers/(w\d+)").expect("valid paper ID regex");
    let mut items = Vec::new();

    for raw in rss.channel.items {
        let raw_title = clean_text(raw.title.as_deref().unwrap_or_default());
        let source_url = clean_text(raw.link.as_deref().unwrap_or_default());
        let guid = clean_text(raw.guid.as_deref().unwrap_or(&source_url));
        let paper_id = paper_id_pattern
            .captures(&source_url)
            .or_else(|| paper_id_pattern.captures(&guid))
            .and_then(|captures| captures.get(1))
            .map(|value| value.as_str().to_string());
        let Some(paper_id) = paper_id else {
            continue;
        };
        let (title, authors) = parse_feed_title(&raw_title);
        let url = source_url
            .split_once('#')
            .map(|(base, _)| base.to_string())
            .unwrap_or_else(|| source_url.clone());
        items.push(FeedSourceItem {
            paper_id,
            title,
            authors,
            abstract_text: clean_text(raw.description.as_deref().unwrap_or_default()),
            url,
            source_url,
            guid,
        });
    }
    Ok(items)
}

pub fn parse_paper(page: &str) -> Result<PaperMetadata, String> {
    let title = first_capture(page, r#"<meta name="citation_title" content="([^"]*)""#)
        .map(|value| clean_text(&value))
        .filter(|value| !value.is_empty())
        .ok_or_else(|| "invalid NBER paper page: missing citation title".to_string())?;
    let author_pattern =
        Regex::new(r#"<meta name="citation_author" content="([^"]*)""#).expect("valid regex");
    let authors = author_pattern
        .captures_iter(page)
        .filter_map(|captures| captures.get(1))
        .map(|value| clean_text(value.as_str()))
        .filter(|value| !value.is_empty())
        .collect();
    let date = first_capture(
        page,
        r#"<meta name="citation_publication_date" content="([^"]*)""#,
    )
    .map(|value| clean_text(&value))
    .unwrap_or_default();
    let raw_id = first_capture(
        page,
        r#"<meta name="citation_technical_report_number" content="([^"]*)""#,
    )
    .unwrap_or_default();
    let id_pattern = Regex::new(r"(?i)^w?0*(\d+)$").expect("valid paper ID regex");
    let numeric_id = id_pattern
        .captures(raw_id.trim())
        .and_then(|captures| captures.get(1))
        .and_then(|value| value.as_str().parse::<u64>().ok())
        .filter(|value| *value > 0)
        .ok_or_else(|| "invalid NBER paper page: missing or invalid citation ID".to_string())?;

    Ok(PaperMetadata {
        paper_id: format!("w{numeric_id}"),
        title,
        authors,
        date,
        abstract_text: extract_section(
            page,
            r#"(?s)<div class="page-header__intro-inner">\s*<p>(.*?)</p>"#,
        )
        .unwrap_or_default(),
        url: None,
        published_version: extract_section(page, r#"(?s)Published Versions</h2>\s*<p>(.*?)</p>"#),
        topic: None,
        programs: None,
    })
}

fn parse_feed_title(raw_title: &str) -> (String, Vec<String>) {
    let Some((title, author_text)) = raw_title.rsplit_once(" -- by ") else {
        return (raw_title.to_string(), Vec::new());
    };
    let authors = author_text
        .split([',', 'ⓡ'])
        .map(str::trim)
        .filter(|author| !author.is_empty())
        .map(str::to_string)
        .collect();
    (title.trim().to_string(), authors)
}

fn extract_section(page: &str, pattern: &str) -> Option<String> {
    first_capture(page, pattern)
        .map(|value| strip_tags(&value))
        .map(|value| clean_text(&value))
        .filter(|value| !value.is_empty())
}

fn first_capture(text: &str, pattern: &str) -> Option<String> {
    Regex::new(pattern)
        .expect("valid extraction regex")
        .captures(text)
        .and_then(|captures| captures.get(1))
        .map(|value| value.as_str().to_string())
}

fn strip_tags(value: &str) -> String {
    Regex::new(r"<[^>]+>")
        .expect("valid tag regex")
        .replace_all(value, "")
        .into_owned()
}

fn clean_text(value: &str) -> String {
    html_escape::decode_html_entities(value)
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

fn repair_feed_xml(xml: &str) -> String {
    let mut repaired = xml.to_string();
    for tag in ["title", "description"] {
        repaired = repair_tag_contents(&repaired, tag);
    }
    repaired
}

fn repair_tag_contents(xml: &str, tag: &str) -> String {
    let opening = format!("<{tag}>");
    let closing = format!("</{tag}>");
    let mut output = String::with_capacity(xml.len());
    let mut remaining = xml;
    while let Some(start) = remaining.find(&opening) {
        let content_start = start + opening.len();
        output.push_str(&remaining[..content_start]);
        let after_opening = &remaining[content_start..];
        let Some(end) = after_opening.find(&closing) else {
            output.push_str(after_opening);
            return output;
        };
        output.push_str(&repair_unsafe_less_than(&after_opening[..end]));
        output.push_str(&closing);
        remaining = &after_opening[end + closing.len()..];
    }
    output.push_str(remaining);
    output
}

fn repair_unsafe_less_than(value: &str) -> String {
    let chars: Vec<char> = value.chars().collect();
    let mut output = String::with_capacity(value.len());
    for (index, character) in chars.iter().enumerate() {
        if *character == '<'
            && chars
                .get(index + 1)
                .is_some_and(|next| next.is_whitespace() || next.is_ascii_digit())
        {
            output.push_str("&lt;");
        } else {
            output.push(*character);
        }
    }
    output
}

fn display_error(error: impl std::fmt::Display) -> String {
    error.to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_feed_items_like_the_cli() {
        let xml = r#"
            <rss><channel><item>
              <title>Useful Paper -- by Ada Lovelace, Grace Hopper</title>
              <link>https://www.nber.org/papers/w12345#rss</link>
              <guid>https://www.nber.org/papers/w12345</guid>
              <description>Effects &amp; evidence</description>
            </item></channel></rss>
        "#;
        let items = parse_feed(xml).unwrap();
        assert_eq!(items.len(), 1);
        assert_eq!(items[0].paper_id, "w12345");
        assert_eq!(items[0].title, "Useful Paper");
        assert_eq!(items[0].authors, ["Ada Lovelace", "Grace Hopper"]);
        assert_eq!(items[0].abstract_text, "Effects & evidence");
        assert_eq!(items[0].url, "https://www.nber.org/papers/w12345");
    }

    #[test]
    fn repairs_unescaped_less_than_in_feed_text() {
        let xml = r#"
            <rss><channel><item>
              <title>Returns < 1 -- by Ada Lovelace</title>
              <link>https://www.nber.org/papers/w12345</link>
              <description>Estimate < 0</description>
            </item></channel></rss>
        "#;
        let items = parse_feed(xml).unwrap();
        assert_eq!(items[0].title, "Returns < 1");
        assert_eq!(items[0].abstract_text, "Estimate < 0");
    }

    #[test]
    fn parses_paper_metadata() {
        let page = r#"
            <meta name="citation_title" content="Test Paper">
            <meta name="citation_author" content="Ada Lovelace">
            <meta name="citation_publication_date" content="2026/07/17">
            <meta name="citation_technical_report_number" content="w00123">
            <div class="page-header__intro-inner"><p>Useful <em>abstract</em>.</p></div>
            <h2>Published Versions</h2><p>Published in <em>Journal</em>.</p>
        "#;
        let paper = parse_paper(page).unwrap();
        assert_eq!(paper.paper_id, "w123");
        assert_eq!(paper.title, "Test Paper");
        assert_eq!(paper.abstract_text, "Useful abstract.");
        assert_eq!(
            paper.published_version.as_deref(),
            Some("Published in Journal.")
        );
    }

    #[test]
    #[ignore = "requires live NBER network access"]
    fn live_feed_refresh_updates_native_database() {
        tokio::runtime::Runtime::new().unwrap().block_on(async {
            let xml = download_text(NBER_FEED_URL).await.unwrap();
            let items = parse_feed(&xml).unwrap();
            assert!(!items.is_empty());

            let page = download_text(&items[0].url).await.unwrap();
            let paper = parse_paper(&page).unwrap();
            assert_eq!(paper.paper_id, items[0].paper_id);

            let db_path = std::env::temp_dir().join(format!(
                "nber-cli-desktop-live-feed-{}.db",
                std::process::id()
            ));
            let _ = std::fs::remove_file(&db_path);
            crate::database::ensure_schema(&db_path).unwrap();
            let result = crate::database::save_feed(&db_path, &items).unwrap();
            assert_eq!(result.fetched_count, items.len());
            assert!(result.total_count > 0);
            let _ = std::fs::remove_file(db_path);
        });
    }
}
