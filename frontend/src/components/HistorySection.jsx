import { useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import RouteCard from './RouteCard'
import { getHistory } from '../api'

const PERIODS = ['1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
const INTERVALS = ['1d', '1wk', '1mo']

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('fr-FR')
}

export default function HistorySection({ symbol }) {
  const [period, setPeriod] = useState('1y')
  const [interval, setInterval] = useState('1d')

  return (
    <RouteCard
      title="Historique des valeurs"
      endpointLabel={`GET /api/securities/${symbol}/history?period=${period}&interval=${interval}`}
      fetcher={() => getHistory(symbol, period, interval)}
    >
      {(data) => {
        const chartData = data.points.map((p) => ({ ...p, dateLabel: formatDate(p.date) }))
        return (
          <div className="history-content">
            <div className="history-controls">
              <label>
                Periode
                <select value={period} onChange={(e) => setPeriod(e.target.value)}>
                  {PERIODS.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Intervalle
                <select value={interval} onChange={(e) => setInterval(e.target.value)}>
                  {INTERVALS.map((i) => (
                    <option key={i} value={i}>
                      {i}
                    </option>
                  ))}
                </select>
              </label>
              <span className="history-hint">
                Change la periode/intervalle puis reclique sur "Tester la route".
              </span>
            </div>

            {chartData.length > 0 ? (
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="dateLabel" minTickGap={40} />
                    <YAxis
                      domain={['auto', 'auto']}
                      tickFormatter={(v) => v.toFixed(0)}
                      width={60}
                    />
                    <Tooltip
                      formatter={(value) => [`${value.toFixed(2)} ${data.currency ?? ''}`, 'Cloture']}
                      labelFormatter={(label) => label}
                    />
                    <Line
                      type="monotone"
                      dataKey="close"
                      stroke="#2563eb"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="note">Aucune donnee pour cette periode/intervalle.</p>
            )}
          </div>
        )
      }}
    </RouteCard>
  )
}
