import streamlit as st
import pandas as pd
from PIL import Image
import os
import sys
import webbrowser
import json
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import markdown
import io
import re
from azure.storage.blob import BlobServiceClient, ContainerSasPermissions


def resource_path(relative_path):
    """
    Gestisce i percorsi dei file sia in modalità di sviluppo che quando l'app è compilata con PyInstaller.
    Restituisce il percorso assoluto della risorsa.
    """
    if relative_path.startswith(('http://', 'https://')):
        return relative_path  # È già un URL, restituiscilo così com'è
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_config():
    """
    Carica la configurazione dal file config.json.
    Restituisce un dizionario con le impostazioni di configurazione.
    """
    with open(resource_path("config.json"), "r", encoding="utf-8") as file:
        return json.load(file)
    

def load_markdown_content(file_path):
    """
    Carica e converte il contenuto di un file markdown in HTML.
    Utilizza l'estensione 'nl2br' per preservare le interruzioni di riga e 'toc' per generare un indice.
    """
    if file_path.startswith(('http://', 'https://')):
        response = requests.get(file_path)
        response.raise_for_status()
        content = response.text
    else:
        with open(resource_path(file_path), 'r', encoding='utf-8') as file:
            content = file.read()
    # Converti il markdown in HTML con i tag <br> per le nuove righe
    html = markdown.markdown(content, extensions=['nl2br', 'toc'])
    return html


@st.cache_data(ttl=3600)  # Cache per un'ora
def extract_examtopics_content(url, selector=".discussion-header-container"):
    """
    Estrae il contenuto di una discussione ExamTopics utilizzando il selettore specificato.
    Rende il contenuto non cliccabile ma scrollabile.
    
    Args:
        url (str): URL della discussione su ExamTopics
        selector (str): Selettore CSS per estrarre il contenuto specifico
        
    Returns:
        str: Contenuto HTML formattato pronto per essere visualizzato
        None: Se il contenuto non può essere estratto
    """
    # Se URL non valido o vuoto, ritorna None
    if not url or not url.startswith('http'):
        return None
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Esegui la richiesta HTTP
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parsa il contenuto
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Estrai il contenitore della discussione usando il selettore specificato
        target_element = soup.select_one(selector)
        
        if not target_element:
            return None
        
        # Estrai tutti gli stili CSS dalla pagina
        style_tags = soup.find_all('style')
        all_styles = "\n".join([style.string for style in style_tags if style.string])
        
        # Estrai i fogli di stile esterni
        stylesheets = []
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                href = link['href']
                if href.startswith('/'):
                    base_url = re.match(r'(https?://[^/]+)', url).group(1)
                    href = base_url + href
                stylesheets.append(f'<link rel="stylesheet" href="{href}">')
        
        # Prepara l'HTML completo con CSS per rendere il contenuto non cliccabile ma scrollabile
        full_html = f"""
        <html>
        <head>
            {''.join(stylesheets)}
            <style>
            {all_styles}
            body {{
                margin: 0;
                padding: 0;
                background: transparent;
            }}
            {selector} {{
                padding: 10px;
                background: white;
                border-radius: 5px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            /* Stile per rendere non cliccabile tutto il contenuto */
            * {{
                pointer-events: none !important;
            }}
            /* Eccezione per permettere lo scrolling */
            html, body {{
                pointer-events: auto !important;
                overflow: auto !important;
            }}
            /* Rimuove qualsiasi evidenziazione o selezione */
            * {{
                user-select: none !important;
                -webkit-user-select: none !important;
                -moz-user-select: none !important;
                -ms-user-select: none !important;
            }}
            /* Rimuovi stili dei link */
            a {{
                color: inherit !important;
                text-decoration: none !important;
                cursor: default !important;
            }}
            </style>
        </head>
        <body>
            {target_element.prettify()}
        </body>
        </html>
        """
        
        return full_html
    
    except Exception as e:
        st.error(f"Errore durante l'estrazione del contenuto: {e}")
        return None


config = load_config()


class CertificationQuizApp:
    def __init__(self, config):
        """
        Inizializza l'applicazione del quiz di certificazione con la configurazione fornita.
        """
        self.df = None
        self.filtered_df = None
        self.correct_answers = 0
        self.total_questions = 0
        self.seen_questions = set()
        self.data_path = config['data_path']
        self.container_name = config.get('container_name')  # Ottieni il container_name dalla config
        
        # Inizializza il client Azure se necessario
        if self.data_path.startswith(('http://', 'https://')):
            self.blob_service_client = self._create_blob_service_client()
            if not self.container_name:
                self.container_name = self._extract_container_name()
        else:
            self.blob_service_client = None
            self.container_name = None

    def _create_blob_service_client(self):
        """
        Crea un client per il servizio Azure Blob Storage usando la SAS key.
        """
        try:
            # Dividi l'URL SAS in base al punto interrogativo
            parts = self.data_path.split('?')
            if len(parts) < 2:
                raise ValueError("URL SAS non valido: manca il token di firma")
            
            # Estrai l'URL di base dell'account
            base_url = parts[0].split('/' + self.container_name)[0] + '/'
            
            # Estrai il token SAS (la parte dopo il ?)
            sas_token = parts[1]
            
            # Crea il client usando l'URL di base e il token SAS
            return BlobServiceClient(account_url=base_url, credential=f"?{sas_token}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    def _extract_container_name(self):
        """
        Estrae il nome del container dall'URL della SAS.
        """
        try:
            url_without_params = self.data_path.split('?')[0]
            container_name = url_without_params.split('/')[-1]
            return container_name
        except Exception as e:
            return None

    def load_cert_config(self, cert_name):
        """
        Carica la configurazione specifica per una certificazione.
        Se non trovata, usa i valori di default.
        """
        default_config = {
            "ai_agent_url": config.get('default_ai_agent_url', "")  # Usa quello globale come fallback
        }
        
        if self.blob_service_client and self.container_name:
            try:
                # Percorso del file di configurazione nel blob storage
                config_path = f"data/{cert_name}/config.json"
                
                # Ottieni il client del container
                container_client = self.blob_service_client.get_container_client(self.container_name)
                blob_client = container_client.get_blob_client(config_path)
                
                try:
                    # Verifica se il blob esiste
                    blob_client.get_blob_properties()
                    
                    # Scarica il contenuto del blob
                    download_stream = blob_client.download_blob()
                    content = download_stream.readall()
                    
                    # Carica il JSON
                    cert_config = json.loads(content.decode('utf-8'))
                    
                    # Aggiorna il dizionario di default con i valori trovati
                    default_config.update(cert_config)
                except Exception as e:
                    pass
            except Exception as e:
                pass
        
        return default_config

    def get_available_certifications(self):
        """
        Recupera l'elenco delle certificazioni disponibili, sia da una fonte locale che remota.
        """
        if self.blob_service_client and self.container_name:
            return self._get_azure_certifications()
        elif self.data_path.startswith(('http://', 'https://')):
            return self._get_remote_certifications(self.data_path)
        else:
            return self._get_local_certifications(self.data_path)

    def _get_azure_certifications(self):
        """
        Recupera l'elenco delle certificazioni da Azure Blob Storage.
        """
        try:
            # Ottieni il client del container
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Elenca tutti i blob nel container
            all_blobs = list(container_client.list_blobs())
            
            # Estrai i nomi delle cartelle di certificazione
            certifications = set()
            for blob in all_blobs:
                parts = blob.name.split('/')
                if len(parts) > 1 and parts[0] == "data":
                    certifications.add(parts[1])
            
            # Verifica quali certificazioni hanno un file database.xlsx
            valid_certifications = []
            for cert in certifications:
                database_path = f"data/{cert}/database.xlsx"
                try:
                    blob_client = container_client.get_blob_client(database_path)
                    properties = blob_client.get_blob_properties()
                    valid_certifications.append(cert)
                except:
                    pass
            
            return valid_certifications
        except Exception as e:
            import traceback
            traceback.print_exc()
            return []

    def _get_remote_certifications(self, url):
        """
        Recupera l'elenco delle certificazioni da una fonte remota.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            certifications = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('/'):
                    cert_name = href.rstrip('/')
                    database_url = urljoin(url, f"{cert_name}/database.xlsx")
                    if self._remote_file_exists(database_url):
                        certifications.append(cert_name)
            
            return certifications
        except requests.RequestException as e:
            return []

    def _get_local_certifications(self, data_dir):
        """
        Recupera l'elenco delle certificazioni da una directory locale.
        """
        return [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d)) and 
                os.path.exists(os.path.join(data_dir, d, "database.xlsx"))]

    def _remote_file_exists(self, url):
        """
        Verifica se un file remoto esiste utilizzando una richiesta HEAD.
        """
        try:
            response = requests.head(url)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def load_certification(self, selected_cert):
        """
        Carica i dati per la certificazione selezionata da un file Excel locale o remoto.
        """
        if self.blob_service_client and self.container_name:
            try:
                # Percorso del file nel blob storage
                blob_path = f"data/{selected_cert}/database.xlsx"
                
                # Ottieni il client del blob
                container_client = self.blob_service_client.get_container_client(self.container_name)
                blob_client = container_client.get_blob_client(blob_path)
                
                # Scarica il contenuto del blob
                download_stream = blob_client.download_blob()
                content = download_stream.readall()
                
                # Leggi il dataframe dal contenuto scaricato
                self.df = pd.read_excel(io.BytesIO(content))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.df = pd.DataFrame()
        elif resource_path(os.path.join(self.data_path, selected_cert, "database.xlsx")).startswith(('http://', 'https://')):
            try:
                file_path = resource_path(os.path.join(self.data_path, selected_cert, "database.xlsx"))
                self.df = pd.read_excel(file_path)
            except Exception as e:
                self.df = pd.DataFrame()
        else:
            file_path = resource_path(os.path.join(self.data_path, selected_cert, "database.xlsx"))
            self.df = pd.read_excel(file_path)
        
        self.df = self.df.dropna(how='all')
        self.df['Topic'] = pd.to_numeric(self.df['Topic'], errors='coerce').fillna(0).astype(int)
        self.df['Numero'] = pd.to_numeric(self.df['Numero'], errors='coerce').fillna(0).astype(int)
        return sorted(self.df['Topic'].unique())

    def filter_questions(self, selected_topic):
        """
        Filtra le domande in base al topic selezionato.
        """
        if selected_topic == "Tutti":
            self.filtered_df = self.df
        else:
            topic_number = int(selected_topic.split()[-1])
            self.filtered_df = self.df[self.df['Topic'] == topic_number]
        self.seen_questions.clear()

    def find_image_file(self, selected_cert, topic, number):
        """
        Trova il file immagine associato a una domanda specifica.
        """
        if self.blob_service_client and self.container_name:
            return self._find_azure_image(selected_cert, topic, number)
        
        image_dir = resource_path(os.path.join(self.data_path, selected_cert, "Domande", f"Topic{topic}"))
        if image_dir.startswith(('http://', 'https://')):
            return self._find_remote_image(image_dir, number)
        else:
            return self._find_local_image(image_dir, number)

    def _find_azure_image(self, selected_cert, topic, number):
        """
        Trova un'immagine in Azure Blob Storage per una domanda specifica.
        """
        try:
            # Definisci il prefisso per la ricerca del blob
            prefix = f"data/{selected_cert}/Domande/Topic{topic}/"
            
            # Ottieni il client del container
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Lista tutti i blob con il prefisso dato
            blobs = list(container_client.list_blobs(name_starts_with=prefix))
            
            # Cerca un blob che corrisponda al numero della domanda
            matching_blob = None
            for blob in blobs:
                file_name = blob.name.split('/')[-1]
                if file_name.startswith(f"{int(number)}."):
                    matching_blob = blob
                    break
            
            if matching_blob:
                # Scarica il blob
                blob_client = container_client.get_blob_client(matching_blob.name)
                download_stream = blob_client.download_blob()
                content = download_stream.readall()
                return io.BytesIO(content)
            else:
                return None
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    def _find_remote_image(self, url, number):
        """
        Cerca un'immagine remota per una domanda specifica.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.startswith(f"{int(number)}."):
                    image_url = urljoin(url, href)
                    # Scarica l'immagine
                    img_response = requests.get(image_url)
                    img_response.raise_for_status()
                    return io.BytesIO(img_response.content)
            return None
        except requests.RequestException as e:
            return None

    def _find_local_image(self, image_dir, number):
        """
        Cerca un'immagine locale per una domanda specifica.
        """
        if not os.path.exists(image_dir):
            return None
        for file in os.listdir(image_dir):
            if file.startswith(f"{int(number)}."):
                return os.path.join(image_dir, file)
        return None

    def get_random_question(self):
        """
        Seleziona una domanda casuale tra quelle non ancora viste.
        """
        if self.filtered_df is None or self.filtered_df.empty:
            return None
        unseen_questions = self.filtered_df[~self.filtered_df.index.isin(self.seen_questions)]
        if unseen_questions.empty:
            self.seen_questions.clear()
            unseen_questions = self.filtered_df
        question = unseen_questions.sample().iloc[0]
        self.seen_questions.add(question.name)
        return question

    def check_answer(self, user_answer, correct_answer):
        """
        Verifica se la risposta dell'utente è corretta.
        """
        return user_answer.strip().upper() == correct_answer.strip().upper()

    def reset_score(self):
        """
        Reimposta il punteggio e le domande viste.
        """
        self.correct_answers = 0
        self.total_questions = 0
        self.seen_questions.clear()

    def get_available_questions_count(self):
        """
        Restituisce il numero di domande disponibili nel set filtrato corrente.
        """
        if self.filtered_df is not None:
            return len(self.filtered_df)
        return 0
        
    def find_question_content(self, link_url):
        """
        Cerca il contenuto web associato al link della domanda.
        Restituisce None se il link non esiste o non è un link di ExamTopics.
        
        Args:
            link_url: URL della domanda (tipicamente da ExamTopics)
            
        Returns:
            str: HTML formattato per il contenuto della domanda
            None: Se il link non esiste o non è di ExamTopics
        """
        if pd.isna(link_url) or not link_url:
            return None
            
        # Verifica se è un link ExamTopics
        if "examtopics.com" in link_url:
            return extract_examtopics_content(link_url)
            
        return None


def main():
    """
    Funzione principale che gestisce l'interfaccia utente e il flusso dell'applicazione.
    Utilizza Streamlit per creare l'interfaccia e gestire le interazioni dell'utente.
    """
    st.set_page_config(page_title="TRR Tool Certificazioni", layout="wide", page_icon=resource_path("static/icon.ico"))
    
    config = load_config()
    
    if 'app' not in st.session_state:
        st.session_state.app = CertificationQuizApp(config)
    app = st.session_state.app

    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = ""
    if 'show_explanation' not in st.session_state:
        st.session_state.show_explanation = False
    if 'current_cert' not in st.session_state:
        st.session_state.current_cert = None
    if 'current_topic' not in st.session_state:
        st.session_state.current_topic = None
    if 'show_guide' not in st.session_state:
        st.session_state.show_guide = False
    if 'cert_config' not in st.session_state:
        st.session_state.cert_config = {}

    st.title("TRR Tool Certificazioni")

    col1, col2 = st.columns([3,1], gap="large")

    with col1:
        col1a, col1b = st.columns(2)
        with col1a:
            available_certs = app.get_available_certifications()
            if not available_certs:
                st.error("Nessuna certificazione trovata. Controlla la configurazione del blob storage.")
            cert = st.selectbox("Seleziona Certificazione:", available_certs if available_certs else ["Nessuna certificazione disponibile"])
        
        if cert and cert != "Nessuna certificazione disponibile":
            if cert != st.session_state.current_cert:
                app.reset_score()
                st.session_state.current_cert = cert
                st.session_state.current_topic = None
                
                # Carica la configurazione specifica della certificazione
                st.session_state.cert_config = app.load_cert_config(cert)
            
            # Mostra un messaggio durante il caricamento
            with st.spinner(f"Caricamento della certificazione {cert}..."):
                topics = app.load_certification(cert)
            
            with col1b:
                topic = st.selectbox("Seleziona Topic:", ["Tutti"] + [f"Topic {t}" for t in topics if t != 0])
            
            if topic != st.session_state.current_topic:
                app.filter_questions(topic)
                st.session_state.current_topic = topic
                st.session_state.current_question = app.get_random_question()
                st.session_state.show_explanation = False
                st.session_state.user_answer = ""

    with col2:
        col2a, col2b = st.columns(2)
        with col2a:
            # Pulsante standard di Streamlit per la guida
            guide_button_text = "Chiudi la Guida" if st.session_state.show_guide else "Guida all'utilizzo"
            if st.button(guide_button_text, use_container_width=True, key="guide_button"):
                st.session_state.show_guide = not st.session_state.show_guide
                st.rerun()
                
        with col2b:
            # Usa l'URL specifico della certificazione se disponibile, altrimenti quello predefinito
            agent_url = st.session_state.cert_config.get('ai_agent_url', config.get('default_ai_agent_url', ""))
            # Pulsante HTML stilizzato per assomigliare ai pulsanti Streamlit
            st.markdown(f"""
            <a href='{agent_url}' target='_blank'>
                <button style='
                    background-color: #7E57C2; 
                    color: white; 
                    border: none; 
                    border-radius: 8px; 
                    padding: 0.5rem 1rem; 
                    font-size: 0.875rem; 
                    line-height: 1.6; 
                    width: 100%; 
                    font-weight: 400; 
                    display: inline-flex; 
                    align-items: center; 
                    justify-content: center; 
                    cursor: pointer;
                '>
                    Chiedi all'Agent AI
                </button>
            </a>
            """, unsafe_allow_html=True)

    if st.session_state.show_guide:
        guide_content = load_markdown_content(config['guide_path'])
        st.markdown(guide_content, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([3,1], gap="large")
        
        with col1:
            if st.session_state.current_question is not None:
                # Ottieni il link della domanda corrente
                link_url = st.session_state.current_question.get('Link', None)
                
                # Verifica se c'è un link ExamTopics valido
                if pd.notna(link_url) and "examtopics.com" in link_url:
                    # Mostra un messaggio durante il caricamento del contenuto
                    with st.spinner("Caricamento contenuto da ExamTopics..."):
                        web_content = app.find_question_content(link_url)
                    
                    if web_content:
                        # Visualizza il contenuto web invece dell'immagine
                        st.components.v1.html(web_content, height=600, scrolling=True)
                    else:
                        # Fallback alle immagini se il contenuto web non può essere estratto
                        st.warning("Impossibile caricare il contenuto da ExamTopics. Caricamento dell'immagine...")
                        _load_question_image(app, cert, st.session_state.current_question)
                else:
                    # Carica l'immagine come al solito
                    _load_question_image(app, cert, st.session_state.current_question)

        with col2:
            st.markdown("### Statistiche Quiz")
            
            stats_col1, stats_col2 = st.columns(2)
            
            with stats_col1:
                percentage = (app.correct_answers / app.total_questions) * 100 if app.total_questions > 0 else 0
                st.metric(label="Punteggio", value=f"{app.correct_answers}/{app.total_questions}")
                st.write(f"Domande disponibili: {app.get_available_questions_count()}")

            with stats_col2:
                st.metric(label="Percentuale", value=f"{percentage:.2f}%") 

            st.markdown("---")  # Linea di separazione

            user_answer = st.text_input("Risposta:", value=st.session_state.user_answer, key="answer_input")
            
            col2a, col2b = st.columns(2)
            with col2a:
                submit_button = st.button("Invia", use_container_width=True, key="submit_button", disabled=st.session_state.show_explanation)
                if submit_button:
                    is_correct = app.check_answer(user_answer, str(st.session_state.current_question['Risposta Esatta']))
                    if is_correct:
                        app.correct_answers += 1
                    app.total_questions += 1
                    st.session_state.user_answer = user_answer
                    st.session_state.show_explanation = True
                    st.rerun()

            with col2b:
                next_button = st.button("Prossima", use_container_width=True, key="next_button", disabled=not st.session_state.show_explanation)
                if next_button:
                    st.session_state.current_question = app.get_random_question()
                    st.session_state.user_answer = ""
                    st.session_state.show_explanation = False
                    st.rerun()

            if st.session_state.show_explanation:
                if app.check_answer(st.session_state.user_answer, str(st.session_state.current_question['Risposta Esatta'])):
                    st.success("Risposta corretta!")
                else:
                    st.error(f"Risposta errata. La risposta corretta era {st.session_state.current_question['Risposta Esatta']}")
                
                st.write(f"**Spiegazione**: {st.session_state.current_question['Commento']}")
                
                # Usa l'URL specifico della certificazione per il link nella spiegazione
                agent_url = st.session_state.cert_config.get('ai_agent_url', config.get('default_ai_agent_url', ""))
                # Modificato per usare st.markdown invece di st.write per garantire la compatibilità
                st.markdown(f"Ancora dubbi? <a href='{agent_url}' target='_blank'>Chiedi all'Agent AI</a>", unsafe_allow_html=True)


# Funzione ausiliaria per il caricamento delle immagini
def _load_question_image(app, cert, question):
    """
    Carica e visualizza l'immagine associata alla domanda.
    
    Args:
        app: L'istanza di CertificationQuizApp
        cert: Il nome della certificazione
        question: La domanda corrente
    """

# Mostra un messaggio durante il caricamento dell'immagine
    with st.spinner("Caricamento immagine..."):
        image_path = app.find_image_file(cert, question['Topic'], question['Numero'])
    
    if image_path:
        try:
            if isinstance(image_path, io.BytesIO):
                image = Image.open(image_path)
            else:
                image = Image.open(image_path)
            
            # Centra l'immagine usando le colonne di Streamlit
            left, center, right = st.columns([1,5,1])
            with center:
                st.image(image, use_container_width=True)
        except Exception as e:
            st.error(f"Errore nel caricamento dell'immagine: {e}")
    else:
        st.warning("Immagine non trovata per questa domanda")


if __name__ == "__main__":
    main()