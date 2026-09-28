# Technical Documentation - CSS Selectors & Implementation

## Analisi HTML e Selettori CSS per Ogni Sito

---

## 1. AMAZON.IT

### URL Ricerca
```
https://www.amazon.it/s?k=ferro+da+stiro
```

### Struttura Lista Prodotti

**Selettore principale:**
```css
div[data-component-type="s-search-result"]  /* Ogni item prodotto */
```

**Campi estratti:**
```
Nome:     h2.s-size-mini span
Link:     a.s-no-outline[href]
Prezzo:   span.a-price-whole
Rating:   span.a-icon-star-small
Reviews:  span[aria-label*="voto"]
```

### Pagina Dettagli Prodotto

**URL formato:** `https://www.amazon.it/dp/{ASIN}`

**Specifiche tecniche:**
```css
table.a-keyvalue tr       /* Tabella specifiche */
  td:first-child           /* Label (es. "Peso") */
  td:nth-child(2)          /* Valore (es. "1,9 kg") */
```

**Fallback (se no tabella):**
```css
ul.a-unordered-list li   /* Feature bullets */
```

### Pagina Review

**URL formato:** `{product_url}#customerReviews`

**Selettore review:**
```css
div[data-hook="review"]

Titolo:     a[data-hook="review-title"]
Testo:      span[data-hook="review-body"]
Rating:     i[data-icon-type="star"]
Autore:     a.a-profile-name
Data:       span[data-hook="review-date"]
Utili:      span[data-hook="helpful-vote-statement"]
```

### Specifiche Amazon

| Campo | Selettore | Fallback |
|-------|-----------|----------|
| Kg | `td:contains('Peso')` | Regex in feature bullets |
| Serbatoio | `td:contains('Capacità')` | Regex pattern `\d+ ml` |
| Cavo | `td:contains('Cavo')` | Regex pattern `\d+ cm` |
| Vapore | `td:contains('Vapore')` | Regex pattern `\d+ livelli` |
| Potenza | `td:contains('Potenza')` | Regex pattern `\d+ w` |

### Code Implementation (amazon_scraper.py)

```python
# Lista prodotti
product_items = soup.find_all('div', {'data-component-type': 's-search-result'})

for item in product_items:
    link = item.find('a', {'class': 's-no-outline'})
    name = item.find('h2', {'class': 's-size-mini'})
    price = item.find('span', {'class': 'a-price-whole'})
```

---

## 2. OPINIONI.IT

### URL Ricerca
```
https://www.opinioni.it/ricerca/ferro%20da%20stiro
```

### Struttura Lista Prodotti

**Selettore principale:**
```css
div.productContainer          /* Contenitore prodotto */
/* Alternativo: div.p-list-item */
```

**Campi estratti:**
```
Nome:     a.productName
Rating:   span.rateValue
Opinioni: span.opinionsNum
Brand:    span.brand
```

### Pagina Dettagli Prodotto

**URL formato:** `https://www.opinioni.it/opinioni/{brand}/{nome}`

**Rating e conteggio opinioni:**
```css
span.productRating           /* Rating complessivo */
span.numOpinions             /* Numero opinioni */
```

**Specifiche tecniche (se presenti):**
```css
div.specifications
  div.spec-item
    span.spec-label          /* Es. "Peso" */
    span.spec-value          /* Es. "1,9 kg" */
```

### Pagina Opinioni/Review

**Stessa URL della pagina dettagli (scrolla):**

**Selettore opinioni:**
```css
div.opinion
  h3.opinionTitle           /* Titolo */
  div.opinionText           /* Testo */
  span.stars                /* Valutazione */
  span.authorName           /* Autore */
  span.opinionDate          /* Data */
  span.usefulVotes          /* Utilità */
```

### Specifiche Opinioni

| Campo | Selettore | Note |
|-------|-----------|------|
| Prezzo | Non disponibile | Opinioni.it non mostra prezzi |
| Specifiche | `div.spec-item` | Spesso incomplete |
| Review | `div.opinion` | Portale specializzato |

### Code Implementation (opinioni_scraper.py)

```python
# Lista prodotti
product_containers = soup.find_all('div', {'class': 'productContainer'})

for container in product_containers:
    link = container.find('a', {'class': 'productName'})
    rating = container.find('span', {'class': 'rateValue'})
```

---

## 3. ROWENTA.IT

### URL Ricerca
```
https://www.rowenta.it/it/prodotti/ferri
```

### Struttura Lista Prodotti

**Selettore principale:**
```css
div.product-item           /* o article.product */
a.product-link [href]
h2.product-name
span.price
span.rating
```

### Pagina Dettagli Prodotto

**URL formato:** `https://www.rowenta.it/it/prodotti/{product-slug}`

**Specifiche tecniche (ben strutturate):**
```css
table.specs-table tr
  td:first-child           /* Label */
  td:last-child            /* Valore */

/* Alternativo */
section.features
  li                       /* Elenco feature */
```

**Mapping Rowenta:**
```
Peso -> "Peso" -> regex
Serbatoio -> "Capacità del serbatoio" -> regex numero
Cavo -> "Lunghezza del cavo" -> regex numero
Vapore -> "Regolazione del vapore" -> testo
Potenza -> "Potenza" -> regex numero
```

### Pagina Review

**Rowenta spesso non ha review nella pagina:**
```css
section.reviews           /* Se presente */
div.review-item
```

### Code Implementation (rowenta_scraper.py)

```python
# Lista prodotti
product_items = soup.find_all('div', {'class': re.compile(r'product.*item')})

# Specifiche
specs_table = soup.find('table', {'class': 'specs-table'})
```

---

## 4. MEDIAWORLD.IT

### URL Ricerca
```
https://www.mediaworld.it/categorie/casa-e-giardino/
                        cucina-piccoli-elettrodomestici/ferri-da-stiro-3
```

### Struttura Lista Prodotti

**Selettore principale:**
```css
div.product, article.product-item
a[href]                   /* Link prodotto */
h2, h3, span.name         /* Nome */
span.price                /* Prezzo */
span.rating               /* Rating */
```

### Pagina Dettagli Prodotto

**URL formato:** `https://www.mediaworld.it/articoli/{product-slug}`

**Specifiche:**
```css
section.specifications
  div.spec-item, tr
    span.label / td:first  /* Label */
    span.value / td:last   /* Valore */
```

### Note Mediaworld

- Rating/reviews non sempre presenti nella ricerca
- Specifiche ben strutturate in sezione "Caratteristiche"
- Prezzi spesso aggiornati in real-time

---

## 5. LIDL.IT

### URL Ricerca
```
https://www.lidl.it/c/casa-e-cucina/elettrodomestici
```

### Struttura Lista Prodotti

**Selettore principale:**
```css
div.product-tile, article.product
a[href]
h2, h3, span.title       /* Nome */
span.price
```

### Pagina Dettagli Prodotto

**URL formato:** `https://www.lidl.it/p/{product-slug}`

**Specifiche:**
```css
section.details, section.features
  li, div                 /* Elenco feature */
```

### Note Lidl

- Non ha review sulla pagina prodotto
- Specifiche spesso in forma testuale (non tabella)
- Prezzi/disponibilità variano per location
- Prodotti spesso stagionali

---

## Regex Patterns Utilizzati

### Prezzo
```python
re.search(r'\d+[.,]\d{2}', text)  # 79,99 o 79.99
```

### Peso (Kg)
```python
re.search(r'(\d+[.,]\d+|\d+)\s*kg', text, re.IGNORECASE)
```

### Serbatoio (ml)
```python
re.search(r'(\d+)\s*ml', text, re.IGNORECASE)
```

### Cavo (cm)
```python
re.search(r'(\d+)\s*cm', text, re.IGNORECASE)
```

### Potenza (W)
```python
re.search(r'(\d+)\s*w(?:att)?', text, re.IGNORECASE)
```

### Rating
```python
re.search(r'\d+[.,]\d+', text)  # 4,5 o 4.5 stelle
```

---

## HTTP Headers e User-Agents

Tutti gli scraper usano:
```python
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': [random user-agent]
}
```

User-agents rotazionati:
- Chrome Windows
- Chrome macOS
- Chrome Linux
- Firefox

---

## Gestione Errori Comuni

### Problema: Selettore non funziona
**Causa:** Sito ha aggiornato HTML
**Soluzione:** 
1. Ispezionare pagina con DevTools (F12)
2. Trovare nuovo selettore
3. Aggiornare config_ferro_da_stiro.json
4. Aggiungere fallback selector nel codice

### Problema: 403 Forbidden
**Causa:** Sito blocca bot
**Soluzione:**
1. Aumentare delay tra richieste
2. Usare rotation user-agent (già implementato)
3. Cambiare IP / usare proxy
4. Usare Selenium con browser headless

### Problema: JavaScript-rendered content
**Causa:** Dati caricati con JS, non visibili in HTML statico
**Soluzione:**
1. Usare Selenium per browser automation
2. Attendere caricamento con WebDriverWait
3. Estrarre dati dopo rendering

---

## Verificare Selettori Localmente

### Con BeautifulSoup
```python
from bs4 import BeautifulSoup
import requests

url = "https://www.amazon.it/s?k=ferro+da+stiro"
html = requests.get(url).content
soup = BeautifulSoup(html, 'html.parser')

# Test selettore
items = soup.find_all('div', {'data-component-type': 's-search-result'})
print(f"Found {len(items)} items")

# Estrarre primo elemento
if items:
    print(items[0].get_text())
```

### Con DevTools Browser
1. Aprire sito in Chrome/Firefox
2. Premere F12 per DevTools
3. Premere Ctrl+Shift+C per Element Inspector
4. Cliccare su elemento
5. Copiare selettore CSS dal DevTools

---

## Performance

### Tempi Medi di Scraping

| Azione | Tempo | Note |
|--------|-------|------|
| Lista prodotti (1 pag) | 5-10s | Con delay 2s |
| Dettagli prodotto | 3-5s | Fetch + parsing |
| 50 review | 15-30s | Dipende carico sito |
| Full scrape (5 siti) | 2-5 min | Sequenziale |

### Ottimizzazioni Possibili

1. **Parallelizzazione**: Scrapare siti simultaneamente
2. **Caching**: Salvare HTML già scrapato
3. **Async**: Usare aiohttp per richieste parallele
4. **Batch**: Fare scraping in batch di pagine

---

## Mappe di Debug

Per debuggare velocemente, creare uno script test:

```python
from amazon_scraper import AmazonScraper

scraper = AmazonScraper({})
products = scraper.scrape_product_list()

print(f"Found {len(products)} products")
if products:
    print("First product:")
    for k, v in products[0].items():
        print(f"  {k}: {v}")
```

Questo stamperà esattamente cosa ha estratto lo scraper dal primo prodotto.
