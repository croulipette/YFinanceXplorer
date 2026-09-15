import RouteCard from './RouteCard'
import { getProfile } from '../api'

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`
}

export default function ProfileSection({ symbol }) {
  return (
    <RouteCard
      title="Secteur d'activite & zone geographique"
      endpointLabel={`GET /api/securities/${symbol}/profile`}
      fetcher={() => getProfile(symbol)}
    >
      {(data) => (
        <div className="profile-content">
          {data.name && <p className="profile-name">{data.name}</p>}

          {(data.sector || data.industry) && (
            <div className="kv-grid">
              <span>Secteur</span>
              <strong>{data.sector || '-'}</strong>
              <span>Industrie</span>
              <strong>{data.industry || '-'}</strong>
            </div>
          )}

          {(data.country || data.region) && (
            <div className="kv-grid">
              <span>Pays</span>
              <strong>{data.country || '-'}</strong>
              <span>Zone geographique</span>
              <strong>{data.region || '-'}</strong>
            </div>
          )}

          {data.sector_weightings && (
            <div className="weightings">
              <p className="weightings-title">Repartition sectorielle du fonds</p>
              <ul>
                {Object.entries(data.sector_weightings)
                  .sort((a, b) => b[1] - a[1])
                  .map(([sector, weight]) => (
                    <li key={sector}>
                      <span className="weighting-label">{sector.replace(/_/g, ' ')}</span>
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
