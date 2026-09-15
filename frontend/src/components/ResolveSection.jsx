import { useState } from 'react'
import { resolveIsin } from '../api'

export default function ResolveSection({ onResolved }) {
  const [isin, setIsin] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [error, setError] = useState(null)
  const [resolved, setResolved] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    const value = isin.trim().toUpperCase()
    if (!value) return

    setStatus('loading')
    setError(null)
    try {
      const data = await resolveIsin(value)
      setResolved(data)
      setStatus('done')
      onResolved(data)
    } catch (err) {
      setError(err.message)
      setStatus('error')
      onResolved(null)
    }
  }

  return (
    <section className="route-card resolve-card">
      <div className="route-card-header">
        <div>
          <h2>1. Resoudre un ISIN</h2>
          <code className="endpoint">GET /api/securities/resolve?isin=...</code>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="resolve-form">
        <input
          type="text"
          placeholder="Ex: FR0000120271"
          value={isin}
          onChange={(e) => setIsin(e.target.value)}
          maxLength={12}
        />
        <button type="submit" disabled={status === 'loading'}>
          {status === 'loading' ? 'Recherche...' : 'Resoudre'}
        </button>
      </form>

      {status === 'error' && <p className="error">{error}</p>}

      {status === 'done' && resolved && (
        <div className="kv-grid">
          <span>Symbole Yahoo</span>
          <strong>{resolved.symbol}</strong>
          <span>Nom</span>
          <strong>{resolved.shortname || '-'}</strong>
          <span>Place</span>
          <strong>{resolved.exchange || '-'}</strong>
          <span>Type</span>
          <strong>{resolved.quote_type || '-'}</strong>
        </div>
      )}
    </section>
  )
}
