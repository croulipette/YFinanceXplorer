import { useState } from 'react'

export default function RouteCard({ title, endpointLabel, fetcher, children }) {
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  async function load() {
    setStatus('loading')
    setError(null)
    try {
      const result = await fetcher()
      setData(result)
      setStatus('done')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <section className="route-card">
      <div className="route-card-header">
        <div>
          <h2>{title}</h2>
          <code className="endpoint">{endpointLabel}</code>
        </div>
        <button onClick={load} disabled={status === 'loading'}>
          {status === 'loading' ? 'Chargement...' : 'Tester la route'}
        </button>
      </div>

      {status === 'error' && <p className="error">{error}</p>}
      {status === 'done' && data && (
        <>
          <div className="route-card-body">{children(data)}</div>
          <details className="raw-json">
            <summary>Reponse JSON brute</summary>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </details>
        </>
      )}
    </section>
  )
}
