# YFinance Explorer

Petite app pour resoudre un code ISIN via Yahoo Finance (yfinance) et explorer,
route par route, les donnees associees : secteur/zone geographique, valeur
courante, historique (graphique) et frais de gestion.

## Architecture

```
backend/   FastAPI + yfinance -> une route par fonctionnalite, donnees formatees en JSON
frontend/  React + Vite -> un bouton "Tester la route" par carte/fonctionnalite
```

Le frontend n'appelle jamais yfinance directement : chaque carte de l'UI
correspond a exactement une route backend.

| Fonctionnalite demandee        | Route backend                                  | Source yfinance |
|---------------------------------|-------------------------------------------------|-----------------|
| ISIN -> symbole Yahoo           | `GET /api/securities/resolve?isin=...`           | `yf.Search(isin)` (Yahoo detecte automatiquement le format ISIN) |
| Secteur d'activite              | `GET /api/securities/{symbol}/profile`           | `Ticker.info["sector"/"industry"]` (actions) ou `Ticker.funds_data.sector_weightings` (ETF/fonds) |
| Secteur/zone geographique       | `GET /api/securities/{symbol}/profile`           | `Ticker.info["country"]`, converti en zone (Europe, Amerique du Nord...) via une table de correspondance interne |
| Valeur courante                 | `GET /api/securities/{symbol}/price`             | `Ticker.fast_info` (last_price, previous_close, currency) |
| Historique (courbe)             | `GET /api/securities/{symbol}/history`           | `Ticker.history(period=, interval=)` |
| Frais de gestion (optionnel)    | `GET /api/securities/{symbol}/fees`              | `Ticker.funds_data.fund_operations` ("Annual Report Expense Ratio"), uniquement pour ETF/fonds |
| Repartition geographique par pays (ETF/fonds) | `GET /api/geography/countries?isin=...` | Scraping de justETF.com (hors yfinance, voir ci-dessous) |

Chaque route degrade proprement (renvoie `note` explicative) quand la source
ne fournit pas la donnee (ex : pas de secteur pour un fonds, pas de frais pour
une action).

### Repartition geographique (justETF)

yfinance/Yahoo Finance n'expose aucune ventilation par pays pour les ETF/fonds
(seulement secteurs et classes d'actifs, voir plus haut). `GET
/api/geography/countries?isin=...` va donc chercher cette donnee sur
justETF.com, qui n'a pas d'API publique documentee : la page profil
(`/en/etf-profile.html?isin=...`) affiche par defaut le top ~4 pays + "Other",
et un lien "Show more" declenche un appel AJAX (framework Apache Wicket) qui
renvoie la liste complete en HTML structure (attributs `data-testid` stables).
`backend/app/services/justetf_service.py` reproduit ces deux requetes HTTP
(pas de navigateur headless, pas de JS execute) et parse le HTML avec
BeautifulSoup. Verifie conforme a `robots.txt` (seuls `/servlet/`, `/link/` et
les recherches/watchlist avec `_wicket` sont interdits).

Points d'attention :
- **Source non officielle** : ce n'est pas un contrat d'API, ca peut casser si
  justETF change son balisage. L'UI affiche toujours explicitement `source:
  "justETF"` + l'URL exacte consultee, pour qu'on sache d'ou vient la donnee.
- Un cache en memoire (6h) evite de solliciter justETF a chaque clic.
- Si l'ISIN ne correspond a aucun ETF sur justETF (ex : une action), la route
  renvoie `countries: null` avec une `note` explicative plutot qu'une erreur.

## Demarrage rapide

```powershell
.\start-all.ps1
```

(ou double-clic sur `start-all.bat`) : ouvre le backend et le frontend chacun
dans sa propre fenetre PowerShell, en creant le venv / les node_modules / le
bundle de certificats au premier lancement si necessaire.

- Backend seul : `backend\start-backend.ps1` (ou `start-backend.bat`)
- Frontend seul : `frontend\start-frontend.ps1` (ou `start-frontend.bat`)

## Lancer le backend manuellement

```powershell
cd backend
python -m venv .venv          # premiere fois seulement
.venv\Scripts\Activate.ps1
pip install -r requirements.txt   # premiere fois seulement
.\scripts\build-ca-bundle.ps1     # genere backend/certs/combined-ca-bundle.pem (non versionne)
$env:SSL_CERT_FILE = "$PWD\certs\combined-ca-bundle.pem"
$env:REQUESTS_CA_BUNDLE = "$PWD\certs\combined-ca-bundle.pem"
$env:CURL_CA_BUNDLE = "$PWD\certs\combined-ca-bundle.pem"
python -m uvicorn app.main:app --port 8000 --reload
```

Documentation interactive (Swagger) : http://127.0.0.1:8000/docs

### Pourquoi le bundle de certificats ?

Le reseau de l'entreprise inspecte le trafic HTTPS (proxy Cato Networks /
CA interne `LDC-DC03-CA`). yfinance (via `curl_cffi`) a besoin d'un certificat
crumb/cookie aupres de `fc.yahoo.com` pour les appels `Ticker.info` et
`funds_data` ; sans ce bundle, ces deux endpoints echouent silencieusement
(les autres, comme `fast_info`/`history`, fonctionnent sans).

`backend/certs/*.pem` n'est **pas** versionne (contient la CA interne de
l'entreprise) : `scripts/build-ca-bundle.ps1` le regenere localement en
combinant les CA publics (certifi) et la CA interne trouvee dans le magasin
Windows. A relancer apres un `git clone` ou une recreation du venv. Sur un
poste sans inspection TLS, les 3 variables d'environnement peuvent simplement
etre omises.

## Lancer le frontend manuellement

```bash
cd frontend
npm install
npm run dev
```

Ouvre l'URL affichee (http://localhost:5173 par defaut). Le serveur de dev
Vite proxifie automatiquement `/api/*` vers `http://127.0.0.1:8000`.

## Limites connues

- La "zone geographique" est deduite du pays du siege social (`info.country`)
  via une table de correspondance simple ; ce n'est pas une repartition des
  revenus par zone (donnee non exposee par yfinance pour les actions).
- Les frais de gestion (`fund_operations`) ne sont pas toujours fournis par
  Yahoo Finance pour tous les ETF (limitation cote donnees, pas cote code) ;
  la route renvoie alors une note explicative plutot qu'une erreur.
