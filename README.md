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
Per una serie di affermazioni da valutare come vere o false, utilizzare "T" per le affermazioni vere e "F" per quelle false:
- Esempio: "TFTF" significa che la prima affermazione è vera (T), la seconda è falsa (F), la terza è vera (T) e la quarta è falsa (F).

### 6. Domande Sì/No (Yes/No)
Stessa logica del punto precedente, ma utilizzare "Y" per Yes e "N" per No.

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

# Aggiungere domande al database

## Struttura della banca dati su Blob Storage

Il TRR Tool Certificazioni utilizza Azure Blob Storage per memorizzare la banca dati delle domande, organizzata secondo la seguente struttura gerarchica:

<div style="white-space: pre-wrap;">
materiale-certificazioni (container)
└── data
    ├── Microsoft DP-700
    │   ├── database.xlsx
    │   ├── config.json (facoltativo)
    │   └── Domande
    │       ├── Topic1
    │       │   ├── 1.png
    │       │   ├── 2.png
    │       │   └── ...
    │       ├── Topic2
    │       │   ├── 1.png
    │       │   └── ...
    │       └── ...
    ├── Microsoft DP-600
    │   ├── database.xlsx
    │   ├── config.json (facoltativo)
    │   └── Domande
    │       └── ...
    └── ...
</div>

### Spiegazione della struttura

1. Il container principale è `materiale-certificazioni`
2. All'interno del container è presente una cartella `data` che contiene tutte le certificazioni
3. Per ogni certificazione (es. DP-700, AZ-104) è presente:
   - Un file `database.xlsx` contenente le domande e le risposte
   - Un file `config.json` (facoltativo) per configurare l'Agent AI specifico della certificazione
   - Una cartella `Domande` contenente le immagini delle domande, organizzate per Topic

### File config.json (facoltativo)

Questo file permette di specificare un Agent AI dedicato per una certificazione. La sua struttura è molto semplice:

```
{
  "ai_agent_url": "https://neurons.reply.com/chat?agentId=ID_SPECIFICO_DELLA_CERTIFICAZIONE"
}
```

Se questo file non è presente, l'applicazione utilizzerà l'Agent AI predefinito configurato nel file `config.json` principale.

## Struttura del file database.xlsx

Il file `database.xlsx` contiene tutte le domande relative a una certificazione. Ogni riga rappresenta una domanda e deve contenere le seguenti colonne:

<table>
  <thead>
    <tr>
      <th>Colonna</th>
      <th>Descrizione</th>
      <th>Obbligatoria</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Tipologia</td>
      <td>Tipo di domanda (es. risposta multipla)</td>
      <td>No</td>
    </tr>
    <tr>
      <td>Topic</td>
      <td>Numero del topic a cui appartiene la domanda</td>
      <td>Sì</td>
    </tr>
    <tr>
      <td>Numero</td>
      <td>Identificativo numerico della domanda, deve corrispondere al nome dell'immagine nella cartella delle immagini</td>
      <td>Sì</td>
    </tr>
    <tr>
      <td>Risposta Esatta</td>
      <td>La risposta corretta alla domanda (vedi il capitolo "Utilizzare TRR Tool Certificazioni" per i formati)</td>
      <td>Sì</td>
    </tr>
    <tr>
      <td>Commento</td>
      <td>Spiegazione sintetica della risposta corretta</td>
      <td>Sì</td>
    </tr>
    <tr>
      <td>Link</td>
      <td>URL alla fonte originale della domanda (es. ExamTopics)</td>
      <td>No</td>
    </tr>
  </tbody>
</table>

### Importante: Correlazione tra Numero e immagini

Il campo `Numero` è fondamentale perché stabilisce la corrispondenza tra la riga nel database e l'immagine della domanda. Per ogni domanda nel file Excel con `Numero = X` e `Topic = Y`, deve esistere un'immagine denominata `X.png` (o altro formato) nella cartella `Domande/TopicY`.

Ad esempio:
- Se nel database c'è una domanda con `Topic = 1` e `Numero = 3`
- Deve esistere un'immagine chiamata `3.png` nella cartella `Domande/Topic1`

## Aggiungere una nuova certificazione

Per aggiungere una nuova certificazione, seguire questi passaggi:

1. Creare una nuova cartella con il nome della certificazione all'interno della cartella `data`
2. Creare il file `database.xlsx` con le colonne sopra descritte
3. Creare la struttura delle cartelle `Domande/TopicX` per ogni topic
4. Aggiungere le immagini delle domande nelle rispettive cartelle dei topic
5. Opzionalmente, aggiungere un file `config.json` se si desidera utilizzare un Agent AI specifico

## Aggiungere nuove domande a una certificazione esistente

Per aggiungere nuove domande a una certificazione esistente:

1. Aggiungere una nuova riga al file `database.xlsx` con tutte le informazioni richieste
2. Assicurarsi che il `Numero` assegnato alla domanda non sia già utilizzato all'interno dello stesso Topic
3. Salvare l'immagine della domanda nella cartella del Topic corrispondente, nominandola con lo stesso numero specificato nel database

## Suggerimenti per la manutenzione

- Mantenere le immagini delle domande di dimensioni ragionevoli per evitare tempi di caricamento eccessivi
- Utilizzare nomi descrittivi per i file di immagine (es. `1.png`, `2.jpg`) per facilitare l'associazione con le domande nel database
- Verificare periodicamente che tutte le domande nel database abbiano un'immagine corrispondente e viceversa
- Assicurarsi che i link alle fonti originali delle domande siano ancora validi

-----


# Installazione del progetto in locale

## Descrizione
TRR Tool Certificazioni è un'applicazione Streamlit progettata per aiutare gli utenti a prepararsi per le certificazioni tecniche. L'applicazione presenta domande casuali da diverse certificazioni e argomenti, permettendo agli utenti di testare le loro conoscenze e ricevere feedback immediato.


## Requisiti
- Python 3.7+


## Installazione

1. **Clonare il repository o scaricare il progetto**
   ```
   git clone https://github.com/bianchimario/Tool_Certificazioni_streamlit
   cd Tool_Certificazioni
   ```

2. **Creare e attivare l'ambiente virtuale**
   - Su Windows:
     ```
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - Su macOS/Linux:
     ```
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
- `default_ai_agent_url`: URL dell'Agent AI di default per assistenza


## Esecuzione
Per avviare l'applicazione, eseguire:
```
streamlit run main.py
```
> **_N.B._** Se il comando _streamlit_ non fosse riconosciuto, eseguire:
        ```
        python -m streamlit run main.py
        ```

