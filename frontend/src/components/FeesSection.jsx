import RouteCard from './RouteCard'
import { getFees } from '../api'

export default function FeesSection({ symbol }) {
  return (
    <RouteCard
      title="Frais de gestion (optionnel)"
      endpointLabel={`GET /api/securities/${symbol}/fees`}
      fetcher={() => getFees(symbol)}
    >
      {(data) => (
        <div className="fees-content">
          {data.applicable ? (
            <div className="kv-grid">
              <span>Frais annuels (TER)</span>
              <strong>
                {data.expense_ratio_percent !== null
                  ? `${data.expense_ratio_percent.toFixed(2)}%`
                  : '-'}
              </strong>
              <span>Moyenne de la categorie</span>
              <strong>
                {data.category_average_percent !== null
                  ? `${data.category_average_percent.toFixed(2)}%`
                  : '-'}
              </strong>
            </div>
          ) : null}
          {data.note && <p className="note">{data.note}</p>}
        </div>
      )}
    </RouteCard>
  )
}
