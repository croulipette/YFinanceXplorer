# YFinance Explorer

Petite app pour explorer les donnees Yahoo Finance (yfinance) et justETF a
partir d'un ISIN ou d'un nom : secteur, zone geographique, valeur courante,
historique, frais de gestion, top holdings — a l'unite ou par lot (portefeuille
CSV).

## Architecture

```
backend/   FastAPI + yfinance/justETF -> une route par fonctionnalite, donnees formatees en JSON
frontend/  React + Vite -> deux onglets : recherche unitaire / analyse par lot
```

Le frontend n'appelle jamais yfinance ni justETF directement : chaque carte de
l'UI correspond a exactement une route backend.

### Onglet "Recherche unitaire"

| Fonctionnalite                  | Route backend                                    | Source |
|----------------------------------|---------------------------------------------------|--------|
| ISIN -> symbole Yahoo            | `GET /api/securities/resolve?isin=...`             | `yf.Search(isin)` |
| Nom/texte -> candidats            | `GET /api/securities/search?query=...`             | `yf.Search(texte)`, plusieurs resultats a choisir |
| Symbole -> ISIN (best-effort)     | `GET /api/securities/{symbol}/isin`                | `Ticker.isin` (yfinance, experimental, echoue souvent) |
| Secteur d'activite               | `GET /api/securities/{symbol}/sector`              | `Ticker.info["sector"/"industry"]` (actions) ou `Ticker.funds_data.sector_weightings` (ETF/fonds) |
| Zone geographique                | `GET /api/geography/countries?isin=...`            | justETF (voir ci-dessous), ETF/fonds uniquement |
| Top 10 positions                 | `GET /api/securities/{symbol}/top-holdings`        | `Ticker.funds_data.top_holdings`, ETF/fonds uniquement |
| Valeur courante                  | `GET /api/securities/{symbol}/price`               | `Ticker.fast_info` |
| Historique (courbe)              | `GET /api/securities/{symbol}/history`             | `Ticker.history(period=, interval=)` |
| Frais de gestion (optionnel)     | `GET /api/securities/{symbol}/fees`                | `Ticker.funds_data.fund_operations`, ETF/fonds uniquement |

Chaque route degrade proprement (renvoie `note` explicative) quand la source
ne fournit pas la donnee (ex : pas de secteur pour un fonds, pas de frais pour
une action). Quand la recherche par nom ne retrouve pas l'ISIN automatiquement,
un champ permet de le completer a la main (necessaire pour la carte geographie).

### Onglet "Recherche par lot"

`POST /api/portfolio/analyze` prend un CSV (voir modele telechargeable dans
l'UI) avec 3 colonnes : `isin`, `quantity` (quantite), `unit_value` (valeur de
part). Delimiteur `,` ou `;` et separateur decimal `,` ou `.` auto-detectes.

Pour chaque ligne : `position_value = quantity * unit_value`, l'ISIN est
resolu (meme route que la recherche unitaire), puis le secteur/geographie/top
holdings de chaque ligne sont agreges, ponderes par `position_value / total` :

- **Secteur** : somme ponderee de `sector` (action, 100% d'un secteur) ou
  `sector_weightings` (fonds) sur toutes les lignes.
- **Geographie** : idem via justETF, uniquement sur les lignes ETF/fonds (le
  `geography_coverage` renvoye indique quelle part du portefeuille est
  couverte, les actions en direct n'y figurant pas).
- **Top holdings (look-through)** : une action detenue en direct compte pour
  100% de son propre poids ; pour un fonds, ses positions (top 10 connu de
  Yahoo) sont ponderees par le poids du fonds dans le portefeuille, puis
  fusionnees par symbole. `holdings_coverage` indique la part couverte ; un
  fonds tres diversifie peut etre sous-represente puisque seul son propre
  top 10 est connu (pas la composition complete).

Les lignes non resolues (ISIN invalide, non trouve, nombre illisible) sont
listees avec leur numero de ligne et la raison, sans faire echouer le reste
de l'analyse.

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

- La zone geographique (justETF) ne couvre que les ETF/fonds, jamais les
  actions individuelles (source specialisee ETF, pas de donnee equivalente
  pour les actions dans l'app).
- Les frais de gestion (`fund_operations`) et le top holdings ne sont pas
  toujours fournis par Yahoo Finance pour tous les ETF (limitation cote
  donnees, pas cote code) ; la route renvoie alors une note explicative
  plutot qu'une erreur.
- La resolution ISIN a partir d'un symbole trouve par recherche texte
  (`Ticker.isin`) est experimentale cote yfinance et echoue pour une partie
  des titres ; completer l'ISIN a la main reste la solution fiable.
- Dans l'analyse par lot, le "top holdings" agrege n'est qu'un look-through
  partiel : seul le top 10 de chaque fonds est connu (pas sa composition
  complete), donc un fonds tres diversifie peut y etre sous-represente.
