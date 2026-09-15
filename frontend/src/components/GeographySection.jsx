import RouteCard from './RouteCard'
import { getCountryBreakdown } from '../api'

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`
}

export default function GeographySection({ isin }) {
  return (
    <RouteCard
      title="Repartition geographique par pays"
      endpointLabel={`GET /api/geography/countries?isin=${isin}`}
      fetcher={() => getCountryBreakdown(isin)}
    >
      {(data) => (
        <div className="geography-content">
          <p className="source-badge">
            Source : <strong>{data.source}</strong> (non officiel, hors yfinance) —{' '}
            <a href={data.source_url} target="_blank" rel="noreferrer">
              page consultee
            </a>
          </p>

          {data.countries && (
            <div className="weightings">
              <ul>
                {Object.entries(data.countries)
                  .sort((a, b) => b[1] - a[1])
                  .map(([country, weight]) => (
                    <li key={country}>
                      <span className="weighting-label">{country}</span>
                      <div className="weighting-bar-track">
                        <div
                          className="weighting-bar-fill"
                          style={{ width: `${Math.min(weight * 100, 100)}%` }}
                        />
                      </div>
                      <span className="weighting-value">{formatPercent(weight)}</span>
                    </li>
                  ))}
              </ul>
            </div>
          )}

          {data.note && <p className="note">{data.note}</p>}
        </div>
      )}
    </RouteCard>
  )
}
