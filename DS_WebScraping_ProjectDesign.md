# DS WebScraping - Analisi Competitiva Prodotti

## Project Design Document

---

## Executive Summary

Questo progetto è un **sistema scalabile di web scraping** per analizzare competitor in diverse categorie di prodotto. L'obiettivo è estrarre dati tecnici, specifiche, prezzi e sentiment da reviews per determinare i migliori valori per le covariate di un nuovo prodotto.

Categoria pilota: **Ferri da stiro** (scalabile a aspirapolveri, frullatori, ecc.)

---

## Obiettivi del progetto

Analizzare **10 ferri da stiro competitor** per identificare:

- ✓ I valori ottimali per ogni covariata (Kg, Serbatoio, Cavo, Vapore, Potenza, Design)
- ✓ Problemi ricorrenti e lamentele dei clienti
- ✓ Sentiment complessivo e fattori di apprezzamento
- ✓ Gap di mercato e opportunità

---

## Covariate da monitorare

| Covariata | Unità | Descrizione |
|-----------|-------|-------------|
| Kg | Chilogrammi | Peso del ferro |
| Serbatoio | ml | Capacità acqua serbatoio |
| Cavo | cm | Lunghezza cavo alimentazione |
| Vapore | Impostazioni | Numero livelli/modalità vapore |
| Potenza | Watt | Potenza elettrica |
| Design | Qualitativo | Colore, materiali, ergonomia |

---

## Architettura di sistema

Il sistema è composto da **7 livelli principali**:

### 1. Data Sources (Fonti dati) Problema principale a mio avviso, cambiamenti struttura web.

**E-commerce:**
- Amazon
- eBay
- Mediaworld

**Siti produttori:**
- Rowenta
- Lidl
- Ariete
- Philips
- Tefal

**Portali di review:**
- Opinioni.it
- Trustpilot
- Google Reviews

### 2. Web Scraping Layer

- **Linguaggio:** Python (BeautifulSoup, Scrapy, Selenium)
- **Approccio:** Mapping dinamico per diversi layout HTML
- **Selettori:** Customizzati per ogni fonte (CSS selectors + XPath)
- **Antibo  t:** Gestione rate limits, user-agent rotation, headless browsing

### 3. Product Selection

- **Criteri di selezione:** Top venduti + Top rated + Diverse fasce di prezzo
- **Campionamento:** 10 prodotti per categoria
- **Copertura segmenti:** Budget, Mid-range, Premium

### 4. Data Processing

**Estrazione specifiche tecniche:**
- Parsing HTML e normalizzazione valori
- Mapping a covariate standard

**Web scraping delle review:**
- Titolo e testo completo
- Rating numerico
- Data postazione
- Numero "utile"

**Sentiment Analysis:**
- Libreria: TextBlob, VADER (NLTK) o spaCy
- Output: label (positivo/neutro/negativo) + score (-1.0 a 1.0)
- Lingua: Italiana

**Keyword Extraction:**
- Metodo: TF-IDF + NLP tagging
- Categorie: problemi, positivi, caratteristiche
- Filtraggio per frequenza minima

### 5. Database Storage

- **Sistema:** PostgreSQL o MongoDB (da scegliere)
- **Tabelle:** products, specs, reviews, sentiment, keywords
- **Archiviazione:** One-shot (no updates richiesti)

### 6. Analysis & Reporting

- Calcolo media, min, max per covariata
- Mappatura sentiment a features
- Identificazione problemi comuni
- Ranking di competitor

### 7. Output (Excel/CSV)

Report con:
- Statistiche per covariata
- Problemi e lamentele comuni
- Raccomandazioni su valori ottimali
- Sentiment score aggregato

---

## Schema del database

### Tabella: products

```
product_id (UUID, PK)
name (VARCHAR 255)
category (VARCHAR 50)           -- es. "ferro_da_stiro"
source (VARCHAR 50)             -- amazon, ebay, rowenta, opinioni.it
url (TEXT)
price_eur (DECIMAL 8,2)
rating_avg (DECIMAL 3,2)        -- voto medio 1-5
review_count (INT)
image_url (TEXT)
scrape_date (TIMESTAMP)
```

### Tabella: specs

```
spec_id (UUID, PK)
product_id (UUID, FK)
kg (DECIMAL 5,2)
serbatoio_ml (INT)
cavo_cm (INT)
vapore_setting (VARCHAR 100)    -- es. "3 livelli"
potenza_w (INT)
design_color (VARCHAR 50)
design_material (VARCHAR 100)
notes (TEXT)
```

### Tabella: reviews

```
review_id (UUID, PK)
product_id (UUID, FK)
rating (INT)                    -- 1-5 stelle
title (VARCHAR 255)
text (TEXT)                     -- testo completo
author (VARCHAR 100)
helpful_count (INT)
date_posted (DATE)
source (VARCHAR 50)
```

### Tabella: sentiment

```
sentiment_id (UUID, PK)
review_id (UUID, FK)
sentiment_label (VARCHAR 20)    -- positivo, neutro, negativo
sentiment_score (DECIMAL 3,2)   -- -1.0 a 1.0
confidence (DECIMAL 3,2)        -- confidence dell'analisi
```

### Tabella: keywords

```
keyword_id (UUID, PK)
review_id (UUID, FK)
keyword (VARCHAR 100)
keyword_type (VARCHAR 50)       -- problema, positivo, caratteristica
frequency (INT)
context (TEXT)                  -- frase contenente il keyword
```

---

## Workflow di implementazione

### Fase 1: Preparazione & Setup (1 settimana)

- [ ] Definire categoria e lista competitor
- [ ] Analizzare struttura HTML delle fonti
- [ ] Creare file di configurazione con selettori CSS/XPath
- [ ] Setup database (PostgreSQL/MongoDB)
- [ ] Creare struttura directory del progetto

### Fase 2: Sviluppo Scraper (1 settimana)

- [ ] Script base per BeautifulSoup/Selenium
- [ ] Sistema di mapping dinamico per diversi siti
- [ ] Gestione errori e retry logic
- [ ] Rate limiting e user-agent rotation
- [ ] Logging e monitoring

### Fase 3: Estrazione dati (1 settimana)

- [ ] Eseguire scraping per ogni fonte
- [ ] Filtrare i 10 prodotti (top seller/rated/prezzo)
- [ ] Estrarre specifiche tecniche
- [ ] Scaricare review e dati di rating

### Fase 4: Data Processing (1.5 settimane)

- [ ] Sentiment analysis su tutte le review
- [ ] Keyword extraction per problemi ricorrenti
- [ ] Aggregazione dati per prodotto
- [ ] Pulizia e normalizzazione dati
- [ ] Validazione qualità dati

### Fase 5: Salvataggio in DB (1 settimana)

- [ ] Inserimento products
- [ ] Inserimento specs
- [ ] Inserimento reviews
- [ ] Inserimento sentiment scores
- [ ] Inserimento keywords
- [ ] Query test e validazione

### Fase 6: Report generation (1 settimana)

- [ ] Query database per statistiche
- [ ] Calcolo media/min/max per covariata
- [ ] Ranking sentiment per feature
- [ ] Generazione Excel/CSV
- [ ] Validazione report

**Timeline totale:** ~6-7 settimane

---

## Dettagli tecnici e best practices

### Gestione della flessibilità HTML

- Creare file `config.json` con selettori per ogni fonte
- Usare fallback chain: CSS selector → XPath → regex
- Loggare fallimenti per debugging
- Test su campione di pagine prima di scale-up

### Sentiment Analysis

- **Libreria:** TextBlob (semplice), VADER, spaCy (advanced)
- **Lingua:** Italiana (usare modelli IT)
- **Output:** label (pos/neg/neutral) + score (-1 a 1)
- **Threshold:** >= 0.3 per positivo, <= -0.3 per negativo

Esempio con TextBlob:
```python
from textblob import TextBlob
text = "Il ferro è ottimo ma il cavo è troppo corto"
sentiment = TextBlob(text).sentiment.polarity  # -0.4 (misto)
```

### Keyword Extraction

- **Metodo:** TF-IDF + NLP tagging
- **Categorie:** 
  - Problemi: "cavo corto", "non scalda", "pesa troppo"
  - Positivi: "scalda bene", "leggero", "buona qualità"
  - Caratteristiche: "serbatoio grande", "vapore continuo"
- **Threshold minimo:** frequency >= 3 per categoria

### Scalabilità per multiple categorie

Struttura directory:
```
/webscraper
  /config
    ferro_da_stiro_config.json
    aspirapolvere_config.json
  /scraper_category
    /ferro_da_stiro
      scraper.py
      processor.py
    /aspirapolvere
      scraper.py
      processor.py
  /utils
    database.py
    sentiment_analyzer.py
    report_generator.py
  main.py
  cli.py
```

CLI usage:
```bash
python cli.py --category ferro_da_stiro --action scrape
python cli.py --category ferro_da_stiro --action process
python cli.py --category ferro_da_stiro --action report
```

---

## Formato report output

Il report Excel dovrà contenere **4 fogli**:

### Foglio 1: Competitive Analysis

| Covariata | Media | Min | Max | Std Dev | Budget (Mean) | Mid-range (Mean) | Premium (Mean) |
|-----------|-------|-----|-----|---------|---------------|------------------|----------------|
| Kg | 1.8 | 1.2 | 2.5 | 0.35 | 1.5 | 1.8 | 2.2 |
| Serbatoio (ml) | 280 | 200 | 400 | 60 | 250 | 280 | 350 |
| Cavo (cm) | 180 | 150 | 210 | 20 | 170 | 180 | 200 |
| Vapore | 2.4 | 1 | 5 | 1.1 | 2 | 2.5 | 4 |
| Potenza (W) | 2400 | 1800 | 3000 | 350 | 2000 | 2400 | 2800 |

**Raccomandazioni:** Scegliere valori nella media-alta della fascia target

### Foglio 2: Sentiment Summary

| Prodotto | Rating Avg | Sentiment Score | % Positivi | % Neutrali | % Negativi | Top Praise | Main Complaint |
|----------|-----------|-----------------|-----------|-----------|-----------|-----------|----------------|
| Philips GC3410/80 | 4.2 | 0.62 | 68% | 18% | 14% | Riscaldamento veloce | Cavo corto |
| Rowenta DW5080 | 4.5 | 0.71 | 75% | 15% | 10% | Qualità costruzione | Peso elevato |
| ... | ... | ... | ... | ... | ... | ... | ... |

### Foglio 3: Problems & Keywords

| Ranking | Problema | Frequenza | N. Prodotti Coinvolti | Sentiment Negativo Avg | Severità |
|---------|----------|-----------|----------------------|----------------------|----------|
| 1 | Cavo troppo corto | 47 | 8 | -0.75 | ALTA |
| 2 | Non scalda uniformemente | 35 | 6 | -0.68 | ALTA |
| 3 | Pesa troppo | 28 | 7 | -0.62 | MEDIA |
| 4 | Cavo rigido | 21 | 5 | -0.58 | MEDIA |
| 5 | Serbatoio piccolo | 19 | 4 | -0.54 | MEDIA |

### Foglio 4: Competitor Details

| Rank | Nome | Brand | Prezzo | Rating | Kg | Serbatoio | Cavo | Vapore | Potenza | Top Problema | Sentiment |
|------|------|-------|--------|--------|-------|-----------|--------|--------|---------|--------------|-----------|
| 1 | DW5080 | Rowenta | €89 | 4.5 | 1.6 | 300 | 200 | 4 | 2400 | Peso | 0.71 |
| 2 | GC3410/80 | Philips | €65 | 4.2 | 1.9 | 280 | 160 | 2 | 2400 | Cavo | 0.62 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

---

## Prossimi passi

1. ✓ Approvare design document APPROVATO
2. [ ] Selezionare primo competitor target I SITI SU CUI VOGLIO FARE WEBSCRAPING PER FERRO DA STIRO SONO: AMAZON, OPINIONI.IT, ROWENTA, MEDIAWORLD, LIDL
3. [ ] Analizzare struttura HTML dei siti PROCEDI
4. [ ] Creare file config.json con selettori PROCEDI
5. [ ] Iniziare development della base scraper SOLO PER FERRO DA STIRO
6. [ ] Testare con 2-3 prodotti prima di scale-up SOLO PER FERRO DA STIRO
7. [ ] Setup database CONFIGURIAMOLO 
8. [ ] Implementare sentiment analysis PROCEDIAMO
9. [ ] Generare report finale PROCEDIAMO

---

**Data:** Settembre 2026  
**Autore:** Project Team  
**Status:** Design Phase  
