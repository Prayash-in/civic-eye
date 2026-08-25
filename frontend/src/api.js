async function request(path, options = {}) {
  const response = await fetch(path, options)

  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (body && body.detail) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
      }
    } catch (_) {
      // non-JSON error body; keep generic message
    }
    throw new Error(detail)
  }

  return response.json()
}

export function createReport(formData) {
  return request('/api/reports', { method: 'POST', body: formData })
}

export function listReports(params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.set(key, value)
  })
  const qs = query.toString()
  return request(`/api/reports${qs ? `?${qs}` : ''}`)
}

export function getReport(id) {
  return request(`/api/reports/${id}`)
}

export function getStats() {
  return request('/api/reports/stats')
}

export function getHealth() {
  return request('/api/health')
}