import { useRef, useState } from 'react'
import { analyzePortfolio } from '../api'

const TEMPLATE_CSV = `isin;quantity;unit_value\nFR0000120271;10;56.30\nIE00B4L5Y983;25;101.42\nIE00B5BMR087;5;708.41\n`

function formatPercent(value) {
  return value === null || value === undefined ? '-' : `${(value * 100).toFixed(1)}%`
}

function WeightBarList({ entries }) {
  return (
    <div className="weightings">
      <ul>
        {entries.map(([label, weight]) => (
          <li key={label}>
            <span className="weighting-label">{label}</span>
            <div className="weighting-bar-track">
              <div className="weighting-bar-fill" style={{ width: `${Math.min(weight * 100, 100)}%` }} />
            </div>
            <span className="weighting-value">{formatPercent(weight)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function downloadTemplate() {
  const blob = new Blob([TEMPLATE_CSV], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'modele-portefeuille.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export default function BatchSearchTab() {
  const fileInputRef = useRef(null)
  const [fileName, setFileName] = useState(null)
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return

    setFileName(file.name)
    setStatus('loading')
    setError(null)
    setResult(null)

    try {
      const data = await analyzePortfolio(file)
      setResult(data)
      setStatus('done')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <div className="app-main">
      <section className="route-card">
        <div className="route-card-header">
          <div>
            <h2>Analyser un portefeuille (CSV)</h2>
            <code className="endpoint">POST /api/portfolio/analyze</code>
          </div>
        </div>

        <p className="note" style={{ marginTop: 12 }}>
          Colonnes attendues (delimiteur , ou ; ; nombres avec , ou . comme separateur decimal) :{' '}
          <strong>isin</strong>, <strong>quantity</strong> (quantite), <strong>unit_value</strong>{' '}
          (valeur de part). La valeur de chaque ligne = quantite &times; valeur de part.
        </p>

        <div className="batch-upload-row">
          <button type="button" onClick={downloadTemplate}>
            Telecharger un modele
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileChange}
          />
          {fileName && <span className="search-result-meta">{fileName}</span>}
        </div>

        {status === 'loading' && <p className="note">Analyse en cours...</p>}
        {status === 'error' && <p className="error">{error}</p>}
      </section>

      {status === 'done' && result && (
        <>
          <section className="route-card">
            <h2>Resume</h2>
            <div className="kv-grid">
              <span>Lignes lues</span>
              <strong>{result.total_lines}</strong>
              <span>Lignes resolues</span>
              <strong>{result.resolved_lines}</strong>
              <span>Valeur totale</span>
              <strong>{result.total_value.toLocaleString('fr-FR', { maximumFractionDigits: 2 })}</strong>
            </div>

            {result.errors.length > 0 && (
              <div className="weightings" style={{ marginTop: 16 }}>
                <p className="weightings-title">Lignes ignorees / en erreur</p>
                <ul className="batch-errors">
                  {result.errors.map((e, i) => (
                    <li key={i}>
                      Ligne {e.row}
                      {e.isin ? ` (${e.isin})` : ''} : {e.reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          <section className="route-card">
            <h2>Repartition sectorielle agregee</h2>
            <p className="source-badge">Source : yfinance (secteur/repartition sectorielle par ligne)</p>
            {Object.keys(result.sector_breakdown).length > 0 ? (
              <WeightBarList
                entries={Object.entries(result.sector_breakdown).sort((a, b) => b[1] - a[1])}
              />
            ) : (
              <p className="note">Aucune donnee sectorielle.</p>
            )}
          </section>

          <section className="route-card">
            <h2>Zone geographique agregee</h2>
            <p className="source-badge">
              Source : justETF — couverture {formatPercent(result.geography_coverage)} du portefeuille
              (ETF/fonds uniquement, les actions detenues en direct n'y figurent pas)
            </p>
            {result.geography_breakdown ? (
              <WeightBarList
                entries={Object.entries(result.geography_breakdown).sort((a, b) => b[1] - a[1])}
              />
            ) : (
              <p className="note">Aucune donnee geographique (pas d'ETF/fonds resolu dans le lot).</p>
            )}
          </section>

          <section className="route-card">
            <h2>Top 10 positions agregees (look-through)</h2>
            <p className="source-badge">
              Source : yfinance — couverture {formatPercent(result.holdings_coverage)} du portefeuille.
              Pour les fonds, seul leur propre top 10 est connu : une ligne de fonds tres diversifie peut
              etre sous-representee ici.
            </p>
            {result.top_holdings.length > 0 ? (
              <ol className="holdings-list">
                {result.top_holdings.map((h) => (
                  <li key={h.symbol}>
                    <span className="holding-symbol">{h.symbol}</span>
                    <span className="holding-name">{h.name || '-'}</span>
                    <div className="weighting-bar-track">
                      <div
                        className="weighting-bar-fill"
                        style={{ width: `${Math.min(h.weight * 100, 100)}%` }}
                      />
                    </div>
                    <span className="weighting-value">{formatPercent(h.weight)}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="note">Aucune position agregee.</p>
            )}
          </section>

          <section className="route-card">
            <h2>Detail des lignes</h2>
            <div className="table-scroll">
              <table className="batch-table">
                <thead>
                  <tr>
                    <th>Ligne</th>
                    <th>ISIN</th>
                    <th>Symbole</th>
                    <th>Nom</th>
                    <th>Type</th>
                    <th>Quantite</th>
                    <th>Valeur part</th>
                    <th>Valeur position</th>
                    <th>Poids</th>
                  </tr>
                </thead>
                <tbody>
                  {result.lines.map((l) => (
                    <tr key={l.row}>
                      <td>{l.row}</td>
                      <td>{l.isin}</td>
                      <td>{l.symbol || '-'}</td>
                      <td>{l.name || '-'}</td>
                      <td>{l.quote_type || '-'}</td>
                      <td>{l.quantity}</td>
                      <td>{l.unit_value}</td>
                      <td>{l.position_value.toLocaleString('fr-FR', { maximumFractionDigits: 2 })}</td>
                      <td>{formatPercent(l.weight)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
