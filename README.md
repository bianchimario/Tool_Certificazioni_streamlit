**Guida all'utilizzo**

[TOC]

-----


# Utilizzare TRR Tool Certificazioni

## Regole generali
- **Case insensitive**: Le risposte sono case insensitive, quindi non fa differenza tra maiuscolo e minuscolo (es. "a" è equivalente ad "A").

## Tipi di domande e formattazione delle risposte

### 1. Selezione multipla (singola risposta)
Per domande con una sola risposta corretta, inserire la lettera corrispondente all'opzione scelta:
- Esempio: "A" o "B" o "C", ecc.

### 2. Selezione multipla (più risposte)
Per domande che richiedono di selezionare più opzioni corrette allo stesso livello, inserire le lettere corrispondenti **in ordine alfabetico**:
- Esempio: "Quali risposte sono vere?" → "ADE" (selezionando le opzioni A, D ed E)

### 3. Multirisposta con box separati
Per domande con più box di risposta separati, inserire le lettere nell'ordine in cui appaiono i box:
- Esempio: "BAC" significa che hai selezionato la seconda opzione (B) per il primo box, la prima opzione (A) per il secondo box, e la terza opzione (C) per il terzo box.

### 4. Ordinamento di elementi
Per domande che richiedono di ordinare degli elementi, inserire le lettere nell'ordine corretto:
- Esempio: "BADC" significa che l'elemento in posizione B va eseguito per primo, seguito dall'elemento in posizione A, poi da D e infine da C.
- Se la prima operazione da eseguire è in seconda posizione, mettere B come prima lettera della risposta.

### 5. Domande Vero/Falso (True/False)
Per una serie di affermazioni da valutare come vere o false, utilizzare "Y" per le affermazioni vere e "N" per quelle false:
- Esempio: "TFTF" significa che la prima affermazione è vera (T), la seconda è falsa (F), la terza è vera (T) e la quarta è falsa (F).

## Esempi pratici

**Domanda tipo 1**: Qual è la capitale dell'Italia?
- A) Milano
- B) Roma
- C) Napoli
- **Risposta corretta**: B

**Domanda tipo 2**: Quali sono linguaggi di programmazione? (seleziona tutte le risposte corrette)
- A) Python
- B) Excel
- C) Java
- D) Word
- E) JavaScript
- **Risposta corretta**: ACE

**Domanda tipo 3**: Abbina ciascun paese con la sua capitale
- Box 1: Italia → A) Madrid, B) Roma, C) Parigi
- Box 2: Francia → A) Parigi, B) Berlino, C) Londra
- Box 3: Germania → A) Amsterdam, B) Vienna, C) Berlino
- **Risposta corretta**: BAC

**Domanda tipo 4**: Ordina le seguenti operazioni per creare un database
- A) Definire le tabelle
- B) Analizzare i requisiti
- C) Implementare le query
- D) Definire le relazioni
- **Risposta corretta**: BADC (prima B, poi A, poi D, infine C)

**Domanda tipo 5**: Indica se le seguenti affermazioni sono vere o false
- A) L'acqua bolle a 100°C a livello del mare
- B) La Terra è piatta
- C) Python è un linguaggio di programmazione
- D) HTML è un linguaggio di programmazione
- **Risposta corretta**: TFTF (A è vera, B è falsa, C è vera, D è falsa)

-----


# Aggiungere domande al database [da completare]
no excel aperto, spiegare domande multi-risposta

- Nome file Excel: "database.xlsx"
- Nome cartella con screenshot domande: "Domande"
- Nome screenshot domanda ```<numeroDomanda.formato>```

<div style="white-space: pre-wrap;">
Tool_Certificazioni/
 ├─> data/
 │      ├─> DP-600/
 │      │      ├─> database.xlsx
 │      │      └─> Domande/
 │      │              └─> Topic1/ → 1.png, 2.jpeg, ...
 │      │
 │      ├─> DP-700/
 │      │      ├─> database.xlsx
 │      │      └─> Domande/
 │      │              ├─> Topic1/ → 1.png, 2.jpeg, ...
 │      │              └─> Topic2/ → 1.png, 2.jpeg, ...
 │      │
 │      └─> ... (altre certificazioni)
 │
 ├─> static/
 │      └─> icon.ico
 │
 ├─> main.py
 ├─> requirements.txt
 └─> config.json
</div>

-----


# Installazione del progetto in locale

## Descrizione
TRR Tool Certificazioni è un'applicazione Streamlit progettata per aiutare gli utenti a prepararsi per le certificazioni tecniche. L'applicazione presenta domande casuali da diverse certificazioni e argomenti, permettendo agli utenti di testare le loro conoscenze e ricevere feedback immediato.


## Requisiti
- Python 3.7+


## Installazione

1. **Clonare il repository o scaricare il progetto**
   ```sh
   git clone <URL_REPOSITORY>
   cd Tool_Certificazioni
   ```

2. **Creare e attivare l'ambiente virtuale**
   - Su Windows:
     ```sh
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - Su macOS/Linux:
     ```sh
     python3 -m venv .venv
     source .venv/bin/activate
     ```

    > **_N.B._** Per uscire dall'ambiente virtuale, eseguire:
        ```
        deactivate
        ```

3. **Installare le dipendenze**
    Sarà necessario installare le seguenti librerie:
    - Streamlit
    - Pandas
    - Pillow (PIL)
    - Requests
    - BeautifulSoup4
    - markdown

    Per farlo, eseguire:
   ```
   pip install -r requirements.txt
   ```

## Configurazione
Il file `config.json` contiene le seguenti chiavi:
- `data_path`: Percorso alla directory dei dati (locale o URL remoto)
- `guide_path`: URL della guida all'utilizzo
- `ai_agent_url`: URL dell'Agent AI per assistenza


## Esecuzione
Per avviare l'applicazione, eseguire:
```
streamlit run main.py
```
> **_N.B._** Se il comando _streamlit_ non fosse riconosciuto, eseguire:
        ```
        python -m streamlit run main.py
        ```


## Note
- Assicurarsi che tutti i file di dati e configurazione siano presenti e accessibili.
- Per l'utilizzo con dati remoti, verificare che gli URL nel `config.json` siano corretti e accessibili.
