# DS WebScraping - Implementation Checklist

## Pre-Development Phase

### ✓ Project Setup
- [ ] Repository Git creato
- [ ] Branch structure definito (main, dev, feature/*)
- [ ] Ambiente Python 3.9+ configurato
- [ ] Virtual environment creato
- [ ] Requirements.txt creato

### ✓ Database Setup
- [ ] PostgreSQL / MongoDB installato e running
- [ ] Database "webscraping" creato
- [ ] Credenziali configurate in .env
- [ ] Script di creazione tabelle preparato
- [ ] Backup strategy definita

### ✓ Configuration Files
- [ ] config_ferro_da_stiro.json personalizzato
- [ ] Selettori CSS/XPath analizzati per ogni fonte
- [ ] Liste competitor definite
- [ ] File di configurazione validato

---

## Sprint 1: Base Scraper & Configuration (1 settimana)

### 1.1 HTML Structure Analysis
- [ ] Scaricato HTML di esempio da 5+ siti
- [ ] Analizzati selettori CSS per products
- [ ] Analizzati selettori CSS per product detail page
- [ ] Analizzati selettori CSS per reviews
- [ ] Documentati fallback selectors
- [ ] Test selettori su campione di pagine

### 1.2 Base Scraper Development
- [ ] Classe `BaseScraper` creata
- [ ] Parser HTML per prodotti
- [ ] Parser HTML per dettagli prodotto
- [ ] Gestione errori e logging
- [ ] Rate limiting implementato
- [ ] User-agent rotation implementato

### 1.3 Source-Specific Scrapers
- [ ] AmazonScraper.py implementato
- [ ] EbayScraper.py implementato
- [ ] RowentaScraper.py implementato
- [ ] OpinioniScraper.py implementato
- [ ] Mapping dinamico tra sorgenti

### 1.4 Testing & Validation
- [ ] Test unitari per parser
- [ ] Test integrazione per una fonte completa
- [ ] Validazione output vs config
- [ ] Documentazione nel README.md

---

## Sprint 2: Product Selection & Filtering (1 settimana)

### 2.1 Product Selection Logic
- [ ] Implementato top-sellers filtering
- [ ] Implementato top-rated filtering
- [ ] Implementato price-range filtering
- [ ] Combinazione criteri multipli (Mix)
- [ ] Selezione 10 prodotti per categoria

### 2.2 Product Deduplication
- [ ] Sistema per identificare duplicati
- [ ] Merge prodotti uguali da fonti diverse
- [ ] Link tra prodotto unico e varianti

### 2.3 Database Integration
- [ ] Connessione al database configurata
- [ ] Schema tables creato
- [ ] ORM/Query builder selezionato
- [ ] Insert logic per tabella products
- [ ] Validazione integrità referenziale

---

## Sprint 3: Review & Detail Pages Scraping (1 settimana)

### 3.1 Review Extraction
- [ ] Parser reviews implementato per ogni fonte
- [ ] Estrazione: testo, rating, data, autore
- [ ] Gestione pagination reviews
- [ ] Max 100 reviews per prodotto
- [ ] Spam filtering (review troppo corte/duplicate)

### 3.2 Technical Specs Extraction
- [ ] Regex patterns per kg
- [ ] Regex patterns per serbatoio
- [ ] Regex patterns per cavo
- [ ] Regex patterns per vapore
- [ ] Regex patterns per potenza
- [ ] Normalizzazione valori e unità

### 3.3 Database Storage
- [ ] Insert logic per tabella reviews
- [ ] Insert logic per tabella specs
- [ ] Error handling per dati mancanti
- [ ] Validazione completezza dati

---

## Sprint 4: NLP Pipeline (1.5 settimane)

### 4.1 Sentiment Analysis
- [ ] Libreria sentiment selezionata (VADER/TextBlob/spaCy)
- [ ] Modello italiano caricato
- [ ] Preprocessing testo review
- [ ] Scoring sentiment (-1 a 1)
- [ ] Classification (pos/neu/neg)
- [ ] Confidence score calcolato

### 4.2 Keyword Extraction
- [ ] TF-IDF implementato
- [ ] Stop words italiano caricati
- [ ] Categorizzazione keywords (problemi/positivi/features)
- [ ] Filtraggio per frequenza minima
- [ ] Context extraction (frase contenente keyword)

### 4.3 Database Storage & Analytics
- [ ] Insert logic per tabella sentiment
- [ ] Insert logic per tabella keywords
- [ ] Query aggregation test
- [ ] Statistica sentiment per prodotto

---

## Sprint 5: Database & Reporting (1 settimana)

### 5.1 Database Optimization
- [ ] Indexes creati per query frequenti
- [ ] Query performance testé
- [ ] Backup strategy implementato
- [ ] Data consistency checks

### 5.2 Report Generation Functions
- [ ] Calcolo media/min/max per covariata
- [ ] Sentiment aggregation per prodotto
- [ ] Problemi ranking per frequenza
- [ ] Positivi ranking per frequenza
- [ ] Segmentazione per fascia prezzo

### 5.3 Excel Export
- [ ] Foglio 1: Competitive Analysis
- [ ] Foglio 2: Sentiment Summary
- [ ] Foglio 3: Problems & Keywords
- [ ] Foglio 4: Competitor Details
- [ ] Formatting e styling applicato

---

## Sprint 6: Testing & Optimization (1 settimana)

### 6.1 End-to-End Testing
- [ ] Test completo 1 categoria da zero a report
- [ ] Validazione qualità dati estrazione
- [ ] Validazione accuracy sentiment
- [ ] Validazione output Excel

### 6.2 Performance Optimization
- [ ] Scraping time profiling
- [ ] Database query optimization
- [ ] Memory usage profiling
- [ ] Parallelizzazione dove possibile

### 6.3 Documentation
- [ ] README.md completato
- [ ] API documentation
- [ ] Troubleshooting guide
- [ ] Examples per ogni comando

---

## Production Deployment

### Deployment Checklist
- [ ] Environment variables definite (.env.example)
- [ ] Database backup automatico
- [ ] Logging centralizato
- [ ] Error monitoring (Sentry/Datadog)
- [ ] CI/CD pipeline configurata
- [ ] Docker image creato (opzionale)

### Monitoring & Maintenance
- [ ] Log analysis dashboard
- [ ] Database health checks
- [ ] Scraper health checks
- [ ] Alert su errori ricorrenti
- [ ] Weekly report generation

---

## Scalability to Multiple Categories

### Code Structure Refactor
- [ ] Generic category launcher
- [ ] Config per categoria nel database
- [ ] CLI interface `python main.py --category ferro_da_stiro`
- [ ] Template per nuove categorie

### New Category Onboarding
1. Creare `config_[categoria].json`
2. Aggiungere source URLs nel config
3. Lanciare scraper: `python main.py --category [categoria]`
4. Validare output
5. Generare report

---

## Risk Management

### Common Issues & Solutions

| Issue | Prevention | Solution |
|-------|-----------|----------|
| Sito cambia struttura HTML | Monitora selettori | Aggiornare config, fallback selector |
| Rate limit / IP ban | Delay, user-agent rotation | Proxy rotation, VPN, API rate limiting |
| Dati duplicati | Dedup logic | Unique constraint DB, merge logic |
| Review spam | Filtering regex | Sentiment anomaly detection |
| Incomplete specs | Fallback fields | Manual entry per data mancante |

---

## Success Criteria

✓ **Data Quality:**
- Almeno 8 su 10 prodotti con specs complete
- Sentiment analysis accuracy >= 80%
- Keyword extraction meaningful >= 70%

✓ **Report Quality:**
- Report generato in < 5 minuti per categoria
- Zero SQL errors
- Formatting corretto in Excel

✓ **Scalability:**
- Aggiunta nuova categoria in < 1 giorno
- Supporto >=5 categorie senza refactor

---

## Timeline Estimate

| Sprint | Settimane | Milestone |
|--------|-----------|-----------|
| Pre-Dev | 1 | Setup completato |
| S1 | 1 | Base scraper funzionante |
| S2 | 1 | 10 prodotti selezionati e salvati |
| S3 | 1 | Reviews e specs estratte |
| S4 | 1.5 | Sentiment e keywords elaborati |
| S5 | 1 | Report Excel generato |
| S6 | 1 | Testing e deploy |
| **Totale** | **~6-7 settimane** | **Production ready** |

---

## Questions for Clarification

### Technical Questions
1. Preferisci PostgreSQL o MongoDB?
2. Vuoi un dashboard per visualizzare dati in real-time?
3. Schedulare esecuzione automatica (es. ogni lunedì)?

### Business Questions
1. Quali sono le top 3 categorie da implementare dopo il ferro?
2. Frequenza di aggiornamento dati (one-shot o periodico)?
3. Chi ha accesso al report? Internal team solo o stakeholders esterni?

### Data Questions
1. Servono dati storici di competitor precedenti?
2. Vuoi tracciare evolution nel tempo?
3. Dati su online vs offline retailers diversi?

---

**Data creazione:** Settembre 2026  
**Last updated:** [Data odierna]  
**Status:** Ready for development
