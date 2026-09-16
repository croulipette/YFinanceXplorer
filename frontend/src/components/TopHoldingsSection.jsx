import RouteCard from './RouteCard'
import { getTopHoldings } from '../api'

function formatPercent(value) {
  return value === null || value === undefined ? '-' : `${(value * 100).toFixed(2)}%`
}

export default function TopHoldingsSection({ symbol }) {
  return (
    <RouteCard
      title="Top 10 positions"
      endpointLabel={`GET /api/securities/${symbol}/top-holdings`}
      fetcher={() => getTopHoldings(symbol)}
    >
      {(data) => (
        <div className="holdings-content">
          {data.holdings && (
            <ol className="holdings-list">
              {data.holdings.map((h) => (
                <li key={h.symbol}>
                  <span className="holding-symbol">{h.symbol}</span>
                  <span className="holding-name">{h.name || '-'}</span>
                  <div className="weighting-bar-track">
                    <div
                      className="weighting-bar-fill"
                      style={{ width: `${Math.min((h.weight ?? 0) * 100, 100)}%` }}
                    />
                  </div>
                  <span className="weighting-value">{formatPercent(h.weight)}</span>
                </li>
              ))}
            </ol>
          )}

          {data.note && <p className="note">{data.note}</p>}
        </div>
      )}
    </RouteCard>
  )
}
