import { apiClient, unwrap } from './client'

export function fetchHealth() {
  return unwrap<{ status: string; version: string; db_path: string }>(apiClient.get('/health'))
}
