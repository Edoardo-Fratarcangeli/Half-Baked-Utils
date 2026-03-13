# Git Search Engine 🔍

**Git Search Engine** è un'applicazione desktop moderna e veloce sviluppata in Python con PyQt6, progettata per esplorare e cercare all'interno della cronologia dei commit di una repository Git con estrema facilità.

![App Icon](app.ico) <!-- Se l'icona è visualizzabile, altrimenti usa un placeholder se necessario -->

## ✨ Caratteristiche principali

-   **🔍 Ricerca Potente**: Filtra i commit per messaggio utilizzando stringhe semplici o **Espressioni Regolari (Regex)**.
-   **📅 Filtri Temporali**: Filtra i commit tra due hash specifici (Since/Until).
-   **🌿 Gestione Branch**: 
    -   Visualizzazione ad albero dei branch locali e remoti.
    -   Possibilità di "pinnare" i branch preferiti in alto per un accesso rapido.
    -   Supporto per la visualizzazione di tutti i branch (`--all`).
-   **🚀 Caricamento Infinito**: Carica i commit in modo fluido durante lo scorrimento (Infinite Scroll).
-   **📋 Integrazione Clipboard**: Copia l'hash di un commit con un semplice doppio-clic.
-   **📝 Esportazione**: Esporta i risultati della ricerca in un file di testo pulito.
-   **🌍 Multi-lingua**: Supporto completo per Italiano e Inglese.
-   **🌓 Design Moderno**: Interfaccia scura e rifinita, ottimizzata per la leggibilità.

## 🛠️ Requisiti

-   Python 3.10+
-   Git installato e configurato nel PATH del sistema.
-   Dipendenze Python:
    -   `PyQt6` (Interfaccia grafica)
    -   `Pillow` (Per la generazione dell'icona, opzionale)

## 🚀 Installazione e Utilizzo

### Esecuzione sorgente
1. Clona la repository.
2. Installa le dipendenze:
   ```bash
   pip install PyQt6
   ```
3. Avvia l'applicazione:
   ```bash
   python git-commit-search.py
   ```

### Funzionamento rapido
1. **Seleziona Repository**: Copia il percorso di una cartella Git e incollalo nell'app tramite il tasto 📋, oppure usa il tasto 📂 per navigare manualmente.
2. **Cerca**: Inserisci una parola chiave o una regex nella barra di ricerca. I risultati appariranno istantaneamente (debounce di 300ms).
3. **Copia**: Fai doppio-clic su un risultato per copiare l'hash del commit negli appunti.

## 💾 Configurazione e Sicurezza

L'applicazione salva le impostazioni (ultima repo usata, lingua, branch pinnati) in un file locale:
`~/.git_commit_search_settings.json`

Non vengono salvati dati sensibili o credenziali Git all'interno dell'applicazione.

## 📦 Compilazione (PyInstaller)
Per generare un eseguibile Windows autonomo:
```bash
pyinstaller GitSearchEngine.spec
```

---
*Sviluppato con ❤️ per rendere la ricerca nei commit Git meno frustrante.*
