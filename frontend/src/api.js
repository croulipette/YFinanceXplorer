const BASE_URL = '/api/securities'

function formatDetail(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || JSON.stringify(item)).join(' ; ')
  }
  return null
}

async function request(path) {
  const res = await fetch(path)
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const message = formatDetail(data?.detail) || `Erreur HTTP ${res.status}`
    throw new Error(message)
  }
  return data
}

export function resolveIsin(isin) {
  return request(`${BASE_URL}/resolve?isin=${encodeURIComponent(isin)}`)
}

export function searchSymbols(query) {
  return request(`${BASE_URL}/search?query=${encodeURIComponent(query)}`)
}

export function getIsinForSymbol(symbol) {
  return request(`${BASE_URL}/${encodeURIComponent(symbol)}/isin`)
}

export function getSector(symbol) {
  return request(`${BASE_URL}/${encodeURIComponent(symbol)}/sector`)
}

export function getPrice(symbol) {
  return request(`${BASE_URL}/${encodeURIComponent(symbol)}/price`)
}

export function getHistory(symbol, period = '1y', interval = '1d') {
  return request(
    `${BASE_URL}/${encodeURIComponent(symbol)}/history?period=${period}&interval=${interval}`
  )
}

export function getTopHoldings(symbol) {
  return request(`${BASE_URL}/${encodeURIComponent(symbol)}/top-holdings`)
}

export function getFees(symbol) {
  return request(`${BASE_URL}/${encodeURIComponent(symbol)}/fees`)
}

export function getCountryBreakdown(isin) {
  return request(`/api/geography/countries?isin=${encodeURIComponent(isin)}`)
}

export async function analyzePortfolio(file) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch('/api/portfolio/analyze', { method: 'POST', body: formData })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const message = formatDetail(data?.detail) || `Erreur HTTP ${res.status}`
    throw new Error(message)
  }
  return data
}
