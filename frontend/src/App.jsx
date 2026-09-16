import { useState } from 'react'
import './App.css'
import SingleSearchTab from './components/SingleSearchTab'
import BatchSearchTab from './components/BatchSearchTab'

function App() {
  const [tab, setTab] = useState('single') // single | batch

  return (
    <div className="app">
      <header className="app-header">
        <h1>YFinance Explorer</h1>
        <p>Renseigne un code ISIN, puis teste chaque route independamment.</p>
      </header>

      <nav className="tabs">
        <button
          type="button"
          className={`tab-button${tab === 'single' ? ' active' : ''}`}
          onClick={() => setTab('single')}
        >
          Recherche unitaire
        </button>
        <button
          type="button"
          className={`tab-button${tab === 'batch' ? ' active' : ''}`}
          onClick={() => setTab('batch')}
        >
          Recherche par lot
        </button>
      </nav>

      <main>{tab === 'single' ? <SingleSearchTab /> : <BatchSearchTab />}</main>
    </div>
  )
}

export default App
