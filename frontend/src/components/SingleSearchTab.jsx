import { useState } from 'react'
import ResolveSection from './ResolveSection'
import SectorSection from './SectorSection'
import GeographySection from './GeographySection'
import TopHoldingsSection from './TopHoldingsSection'
import PriceSection from './PriceSection'
import HistorySection from './HistorySection'
import FeesSection from './FeesSection'

export default function SingleSearchTab() {
  const [resolved, setResolved] = useState(null)

  return (
    <div className="app-main">
      <ResolveSection onResolved={setResolved} />

      {resolved && (
        <div key={resolved.symbol} className="app-main">
          <SectorSection symbol={resolved.symbol} />
          {resolved.isin && <GeographySection isin={resolved.isin} />}
          <TopHoldingsSection symbol={resolved.symbol} />
          <PriceSection symbol={resolved.symbol} />
          <HistorySection symbol={resolved.symbol} />
          <FeesSection symbol={resolved.symbol} />
        </div>
      )}
    </div>
  )
}
