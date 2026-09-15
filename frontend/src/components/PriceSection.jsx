import RouteCard from './RouteCard'
import { getPrice } from '../api'

export default function PriceSection({ symbol }) {
  return (
    <RouteCard
      title="Valeur courante"
      endpointLabel={`GET /api/securities/${symbol}/price`}
      fetcher={() => getPrice(symbol)}
    >
      {(data) => {
        const isUp = (data.change ?? 0) >= 0
        return (
          <div className="price-content">
            <div className="price-main">
              <span className="price-value">
                {data.last_price?.toFixed(2) ?? '-'} {data.currency}
              </span>
              {data.change !== null && (
                <span className={`price-change ${isUp ? 'up' : 'down'}`}>
                  {isUp ? '+' : ''}
                  {data.change.toFixed(2)} ({isUp ? '+' : ''}
                  {data.change_percent.toFixed(2)}%)
                </span>
              )}
            </div>
            <div className="kv-grid">
              <span>Cloture precedente</span>
              <strong>
                {data.previous_close?.toFixed(2) ?? '-'} {data.currency}
              </strong>
              <span>Recupere le</span>
              <strong>{new Date(data.as_of).toLocaleString('fr-FR')}</strong>
            </div>
          </div>
        )
      }}
    </RouteCard>
  )
}
