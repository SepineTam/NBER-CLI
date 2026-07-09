import axios from 'axios'
import type { ApiEnvelope } from '../types'

const DEFAULT_BASE_URL = 'http://127.0.0.1:31527/api/v1'

export const apiClient = axios.create({
  baseURL: DEFAULT_BASE_URL,
  timeout: 15000,
})

export function setApiBaseUrl(baseURL: string) {
  apiClient.defaults.baseURL = baseURL
}

export async function unwrap<T>(request: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  const response = await request
  if (response.data.code !== 0) {
    throw new Error(response.data.message || 'Request failed')
  }
  return response.data.data
}

export function readableError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data as Partial<ApiEnvelope<unknown>> | undefined
    return payload?.message || error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unknown error'
}
