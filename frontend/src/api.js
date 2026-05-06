const configuredBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').trim()

export const apiBaseUrl = configuredBase.endsWith('/')
  ? configuredBase.slice(0, -1)
  : configuredBase

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

export async function apiRequest(path, options = {}) {
  const { method = 'GET', body, headers = {} } = options

  const requestHeaders = {
    ...headers,
  }

  const requestOptions = {
    method,
    credentials: 'include',
    headers: requestHeaders,
  }

  if (body !== undefined) {
    requestHeaders['Content-Type'] = 'application/json'
    requestOptions.body = JSON.stringify(body)
  }

  const response = await fetch(`${apiBaseUrl}${path}`, requestOptions)

  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')

  let payload = null
  if (isJson) {
    try {
      payload = await response.json()
    } catch {
      payload = null
    }
  }

  if (!response.ok) {
    throw new ApiError(payload?.message || `HTTP ${response.status}`, response.status, payload)
  }

  return payload
}
