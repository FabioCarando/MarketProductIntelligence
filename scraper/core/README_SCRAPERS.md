# DS WebScraping - Scraper di Ferri da Stiro

Progetto completo di web scraping per analizzare ferri da stiro competitor da 5 siti italiani.

## Siti Scrapati

1. **Amazon.it** - E-commerce con review e rating
2. **Opinioni.it** - Portale italiano specializzato in review di prodotti
3. **Rowenta.it** - Sito ufficiale del produttore
4. **Mediaworld.it** - Retailer di elettrodomestici
5. **Lidl.it** - Supermercato online

## Architettura

```
├── base_scraper.py          # Classe base con metodi comuni
├── amazon_scraper.py        # Scraper Amazon.it
├── opinioni_scraper.py      # Scraper Opinioni.it
├── rowenta_scraper.py       # Scraper Rowenta.it
├── retailer_scrapers.py     # Scraper Mediaworld + Lidl
├── main_scraper.py          # Orchestrator principale
├── config_ferro_da_stiro.json  # Configurazione
├── requirements.txt         # Dipendenze Python
└── README.md               # Questo file
```

## Installazione

### 1. Clonare il repository
```bash
git clone <repo_url>
cd ds-webscraping
```

### 2. Creare virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 3. Installare dipendenze
```bash
pip install -r requirements.txt
```

### 4. Download modelli NLTK (per sentiment analysis)
```bash
python3 -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

## Utilizzo

### Esecuzione Rapida (Test)

```bash
python main_scraper.py
```

Questo esegue:
- 1 pagina di ricerca per sito
- Estrae dettagli di 5 prodotti
- Scrapa review di 3 prodotti
- Esporta dati in JSON e CSV

### Esecuzione Personalizzata

Crea uno script `run_scraper.py`:

```python
from main_scraper import ScraperOrchestrator

orchestrator = ScraperOrchestrator()

# Configurazione personalizzata
orchestrator.run_full_scrape(
    max_pages=2,                    # 2 pagine per sito
    product_details_limit=20,       # Dettagli di 20 prodotti
    reviews_limit=10                # Review di 10 prodotti
)
```

Poi esegui:
```bash
python run_scraper.py
```

### Scraping per Singolo Sito

```python
from amazon_scraper import AmazonScraper

scraper = AmazonScraper({
    'delay_between_requests': 2,
    'timeout_seconds': 30
})

# Lista prodotti
products = scraper.scrape_product_list()

# Dettagli di un prodotto
details = scraper.scrape_product_details(products[0]['url'])

# Review di un prodotto
reviews = scraper.scrape_reviews(products[0]['url'], max_reviews=50)
```

## Output

Il programma genera 3 file:

### 1. `products.json`
JSON con lista di TUTTI i prodotti scrapati:
```json
[
  {
    "source": "Amazon.it",
    "name": "Philips GC3410/80 Ferro da Stiro",
    "price_eur": 65.99,
    "rating": 4.2,
    "review_count": 189,
    "url": "https://amazon.it/...",
    "kg": 1.9,
    "serbatoio_ml": 280,
    "cavo_cm": 160,
    "vapore_setting": "2 livelli",
    "potenza_w": 2400,
    "design_color": "Bianco",
    "scrape_date": "2026-09-28T10:30:00"
  },
  ...
]
```

### 2. `products.csv`
Versione tabulare dei prodotti per Excel/Sheets:
```csv
source,name,price_eur,rating,review_count,url,kg,serbatoio_ml,cavo_cm,vapore_setting,potenza_w,design_color
Amazon.it,Philips GC3410/80,65.99,4.2,189,...,1.9,280,160,2 livelli,2400,Bianco
...
```

### 3. `reviews.json`
JSON con tutte le review scrapate:
```json
[
  {
    "source": "Amazon.it",
    "author": "Marco R.",
    "rating": 5,
    "title": "Eccellente qualità",
    "text": "Ferro fantastico, riscalda rapidamente...",
    "date_posted": "12 settembre 2026",
    "helpful_count": 47,
    "product_id": "Philips GC3410/80",
    "product_url": "https://amazon.it/..."
  },
  ...
]
```

### 4. `scraper.log`
Log completo dell'esecuzione con dettagli di ogni passo

## Configurazione

Il file `config_ferro_da_stiro.json` permette di customizzare:

### Abilitare/disabilitare siti
```json
{
  "sources": {
    "amazon_it": {"enabled": true},
    "opinioni_it": {"enabled": true},
    "rowenta_it": {"enabled": true},
    "mediaworld_it": {"enabled": false},
    "lidl_it": {"enabled": false}
  }
}
```

### Parametri scraping
```json
{
  "scraping_settings": {
    "delay_between_requests": 2,
    "max_retries": 3,
    "timeout_seconds": 30,
    "javascript_rendering": true
  }
}
```

### Mapping covariate
```json
{
  "covariate_mapping": {
    "kg": "Peso in kilogrammi",
    "serbatoio": "Capacità serbatoio in millilitri",
    "cavo": "Lunghezza cavo in centimetri",
    "vapore": "Numero livelli/modalità vapore",
    "potenza": "Potenza in watt",
    "design": "Colore, materiali, ergonomia"
  }
}
```

## Struttura Dati Prodotto

Ogni prodotto estratto contiene:

```python
{
    'source': str,              # Nome source (Amazon.it, Opinioni.it, etc.)
    'name': str,                # Nome prodotto
    'price_eur': float,         # Prezzo in euro
    'rating': float,            # Voto 1-5 stelle
    'review_count': int,        # Numero review/opinioni
    'url': str,                 # URL del prodotto
    'kg': float,                # Peso in kg
    'serbatoio_ml': int,        # Capacità serbatoio in ml
    'cavo_cm': int,             # Lunghezza cavo in cm
    'vapore_setting': str,      # Tipo/livelli vapore
    'potenza_w': int,           # Potenza in watt
    'design_color': str,        # Colore
    'design_material': str,     # Materiale
    'scrape_date': str          # Data scraping
}
```

## Struttura Dati Review

```python
{
    'source': str,              # Nome source
    'product_id': str,          # ID/nome prodotto
    'product_url': str,         # URL prodotto
    'author': str,              # Nome autore review
    'rating': float,            # Voto 1-5
    'title': str,               # Titolo review
    'text': str,                # Testo completo review
    'date_posted': str,         # Data postazione
    'helpful_count': int        # Numero "utile"
}
```

## Troubleshooting

### "Connection refused"
```
Soluzione: Aumentare delay_between_requests in config
delay_between_requests: 3-5 secondi
```

### "403 Forbidden"
```
Soluzione: Il sito ha bloccato il bot. Prova:
1. Cambiare user-agent (già implementato)
2. Usare Selenium con headless browser
3. Usare proxy o VPN
```

### "No products found"
```
Possibili cause:
1. Selettore CSS cambiato (sito aggiornato)
2. Paginazione differente (aggiornare config)
3. JavaScript rendering necessario (usare Selenium)

Soluzione: Ispezionare pagina e aggiornare config_ferro_da_stiro.json
```

### "Timeout"
```
Aumentare timeout_seconds:
"timeout_seconds": 60  # Aumenta da 30 a 60 secondi
```

## Performance Tips

1. **Parallelizzazione**: Scrapare da multiple source contemporaneamente
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    for source_name, scraper in scrapers.items():
        executor.submit(scraper.scrape_product_list)
```

2. **Caching**: Salvare pagine HTML per non riscrapare
```python
import pickle
with open('cache.pkl', 'rb') as f:
    cached_html = pickle.load(f)
```

3. **Batch Processing**: Fare scraping in orari non di picco

## Legal & Ethical

- Rispettare `robots.txt` di ogni sito
- Usare `delay_between_requests` > 1-2 secondi
- Non sovraccaricare i server
- Verificare Terms of Service di ogni sito
- Usare i dati per analisi interna solo

## Prossimi Step

1. **Sentiment Analysis**: Processare reviews per sentiment
```bash
python nlp_processor.py
```

2. **Report Generation**: Generare report Excel finale
```bash
python generate_report.py
```

3. **Database Storage**: Salvare in PostgreSQL/MongoDB
```bash
python db_loader.py
```

## Contatti & Support

Per domande o issue:
- Aprire un GitHub issue
- Contattare il team di data engineering

## Licenza

Proprietario - Uso interno only
