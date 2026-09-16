import { useState } from 'react'
import { resolveIsin, searchSymbols, getIsinForSymbol } from '../api'

const ISIN_PATTERN = /^[A-Z]{2}[A-Z0-9]{9}[0-9]$/

export default function ResolveSection({ onResolved }) {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | resolved | picking | error
  const [error, setError] = useState(null)
  const [resolved, setResolved] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [pickingSymbol, setPickingSymbol] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    const value = query.trim()
    if (!value) return

    setStatus('loading')
    setError(null)
    setCandidates([])
    onResolved(null)

    try {
      if (ISIN_PATTERN.test(value.toUpperCase())) {
        const data = await resolveIsin(value.toUpperCase())
        setResolved(data)
        setStatus('resolved')
        onResolved(data)
      } else {
        const data = await searchSymbols(value)
        if (data.results.length === 0) {
          setError(`Aucun resultat pour "${value}".`)
          setStatus('error')
        } else {
          setCandidates(data.results)
          setStatus('picking')
        }
      }
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  async function handlePick(candidate) {
    setPickingSymbol(candidate.symbol)
    // L'ISIN n'est pas fourni par la recherche par nom : on tente une
    // resolution best-effort (yfinance experimental, peut echouer).
    let isin = null
    try {
      const isinData = await getIsinForSymbol(candidate.symbol)
      isin = isinData.isin
    } catch {
      // best-effort : on continue sans ISIN
    }

    const data = {
      isin,
      symbol: candidate.symbol,
      shortname: candidate.shortname,
      exchange: candidate.exchange,
      quote_type: candidate.quote_type,
    }
    setResolved(data)
    setStatus('resolved')
    setCandidates([])
    setPickingSymbol(null)
    onResolved(data)
  }

  return (
    <section className="route-card resolve-card">
      <div className="route-card-header">
        <div>
          <h2>1. Rechercher un titre</h2>
          <code className="endpoint">
            GET /api/securities/resolve?isin=... ou GET /api/securities/search?query=...
          </code>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="resolve-form">
        <input
          type="text"
          placeholder="ISIN (FR0000120271) ou nom (Msci World)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={status === 'loading'}>
          {status === 'loading' ? 'Recherche...' : 'Rechercher'}
        </button>
      </form>

      {status === 'error' && <p className="error">{error}</p>}

      {status === 'picking' && (
        <ul className="search-results">
          {candidates.map((c) => (
            <li key={c.symbol}>
              <button
                type="button"
                className="search-result-item"
                onClick={() => handlePick(c)}
                disabled={pickingSymbol !== null}
              >
                <span className="search-result-symbol">{c.symbol}</span>
                <span className="search-result-name">{c.shortname || '-'}</span>
                <span className="search-result-meta">
                  {c.exchange || '-'} · {c.quote_type || '-'}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {status === 'resolved' && resolved && (
        <div className="kv-grid">
          <span>Symbole Yahoo</span>
          <strong>{resolved.symbol}</strong>
          <span>Nom</span>
          <strong>{resolved.shortname || '-'}</strong>
          <span>Place</span>
          <strong>{resolved.exchange || '-'}</strong>
          <span>Type</span>
          <strong>{resolved.quote_type || '-'}</strong>
          {resolved.isin && (
            <>
              <span>ISIN</span>
              <strong>{resolved.isin}</strong>
            </>
          )}
        </div>
      )}
    </section>
  )
}
