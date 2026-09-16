import { useState } from 'react'
import './App.css'
import ResolveSection from './components/ResolveSection'
import SectorSection from './components/SectorSection'
import GeographySection from './components/GeographySection'
import PriceSection from './components/PriceSection'
import HistorySection from './components/HistorySection'
import FeesSection from './components/FeesSection'

function App() {
  const [resolved, setResolved] = useState(null)

  return (
    <div className="app">
      <header className="app-header">
        <h1>YFinance Explorer</h1>
        <p>Renseigne un code ISIN, puis teste chaque route independamment.</p>
      </header>

      <main className="app-main">
        <ResolveSection onResolved={setResolved} />

        {resolved && (
          <div key={resolved.symbol} className="app-main">
            <SectorSection symbol={resolved.symbol} />
            {resolved.isin && <GeographySection isin={resolved.isin} />}
            <PriceSection symbol={resolved.symbol} />
            <HistorySection symbol={resolved.symbol} />
            <FeesSection symbol={resolved.symbol} />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
