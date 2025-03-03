**Guida all'utilizzo**

[TOC]

-----


# Utilizzare TRR Tool Certificazioni [da completare]
[da completare, spiegare come rispondere]

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