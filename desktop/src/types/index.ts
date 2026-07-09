export interface ApiEnvelope<T> {
  code: number
  data: T
  message: string
}

export interface FeedItem {
  paper_id: string
  title: string
  authors: string[]
  abstract: string
  url: string
  source_url: string
  guid: string
  first_seen_at: string
  last_seen_at: string
  is_read: boolean
}

export interface FeedList {
  items: FeedItem[]
  total_count: number
  limit: number
  offset: number
  last_successful_fetch_at: string | null
}

export interface FeedRefreshResult {
  new_count: number
  total_count: number
  fetched_count: number
  last_successful_fetch_at: string | null
}

export interface Paper {
  paper_id: string
  title: string
  authors: string[]
  date: string
  abstract: string
  url: string | null
  pdf_url: string | null
  published_version: string | null
  topic: string | null
  programs: string | null
  is_read: boolean
  from_cache: boolean
}

export interface Settings {
  server_port: number
  feed_refresh_interval_minutes: number
  config_path: string
  db_path: string
  log_dir: string
}

export interface DesktopConfig {
  server_port: number
  feed_refresh_interval_minutes: number
  api_base_url: string
  config_path: string
  db_path: string
  log_dir: string
}

export interface SidecarStatus {
  ready: boolean
  port: number
  message: string
}
