import streamlit as st
import pandas as pd
from PIL import Image
import os
import sys
import json
import requests
import markdown
import io
from azure.storage.blob import BlobServiceClient


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


def initialize_blob_cache(app):
    """
    Inizializza la cache dei blob scaricando tutti i blob necessari una sola volta.
    """
    if 'blob_cache' not in st.session_state:
        try:
            # Ottieni il client del container
            container_client = app.blob_service_client.get_container_client(app.container_name)
            
            # Elenca tutti i blob nel container
            st.session_state.all_blobs = list(container_client.list_blobs())
            
            # Crea una mappa dei blob per un accesso più efficiente
            blob_map = {}
            certifications = set()
            
            for blob in st.session_state.all_blobs:
                blob_map[blob.name] = blob
                
                # Estrai le certificazioni
                parts = blob.name.split('/')
                if len(parts) > 1 and parts[0] == "data":
                    certifications.add(parts[1])
            
            # Crea un dizionario per le certificazioni valide
            valid_certifications = []
            cert_configs = {}
            cert_databases = {}
            cert_images = {}
            
            for cert in certifications:
                database_path = f"data/{cert}/database.xlsx"
                
                # Verifica se esiste il database della certificazione
                if database_path in blob_map:
                    valid_certifications.append(cert)
                    
                    # Carica la configurazione (se esiste)
                    config_path = f"data/{cert}/config.json"
                    if config_path in blob_map:
                        blob_client = container_client.get_blob_client(config_path)
                        download_stream = blob_client.download_blob()
                        content = download_stream.readall()
                        cert_configs[cert] = json.loads(content.decode('utf-8'))
                    
                    # Carica il database
                    blob_client = container_client.get_blob_client(database_path)
                    download_stream = blob_client.download_blob()
                    content = download_stream.readall()
                    df = pd.read_excel(io.BytesIO(content))
                    cert_databases[cert] = df
                    
                    # Organizza le immagini per topic e numero
                    cert_images[cert] = {}
                    img_prefix = f"data/{cert}/Domande/"
                    for blob in st.session_state.all_blobs:
                        if blob.name.startswith(img_prefix):
                            # Estrai topic e numero dall'immagine
                            path_parts = blob.name.split('/')
                            if len(path_parts) > 4 and path_parts[3].startswith("Topic"):
                                topic = path_parts[3].replace("Topic", "")
                                file_name = path_parts[4]
                                
                                # Estrai il numero dall'inizio del nome del file
                                number_parts = file_name.split('.')
                                if len(number_parts) >= 2:
                                    try:
                                        number = int(number_parts[0])
                                        
                                        # Aggiungi alla struttura delle immagini
                                        if topic not in cert_images[cert]:
                                            cert_images[cert][topic] = {}
                                        
                                        cert_images[cert][topic][number] = blob.name
                                    except ValueError:
                                        pass
            
            # Crea anche una cache delle immagini già scaricate
            image_content_cache = {}
            
            # Salva tutto nella session_state
            st.session_state.blob_cache = {
                'valid_certifications': valid_certifications,
                'cert_configs': cert_configs,
                'cert_databases': cert_databases,
                'cert_images': cert_images,
                'blob_map': blob_map,
                'image_content_cache': image_content_cache
            }
            
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            st.error(f"Errore nell'inizializzazione della cache: {str(e)}")
            return False
    return True


# Carica la configurazione una sola volta all'inizio
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

    def load_cert_config(self, cert_name):
        """
        Carica la configurazione specifica per una certificazione dalla cache.
        """
        default_config = {
            "ai_agent_url": config.get('default_ai_agent_url', "")  # Usa quello globale come fallback
        }
        
        if self.blob_service_client and self.container_name:
            if 'blob_cache' in st.session_state and cert_name in st.session_state.blob_cache['cert_configs']:
                default_config.update(st.session_state.blob_cache['cert_configs'][cert_name])
            else:
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
                    except Exception:
                        pass
                except Exception:
                    pass
        
        return default_config

    def get_available_certifications(self):
        """
        Recupera l'elenco delle certificazioni disponibili dalla cache.
        """
        if not self.blob_service_client or not self.container_name:
            return []
            
        if 'blob_cache' in st.session_state:
            return st.session_state.blob_cache['valid_certifications']
        
        # Se la cache non è disponibile, restituisci una lista vuota
        # oppure visualizza un messaggio di errore
        st.error("Cache non inizializzata correttamente. Riavvia l'applicazione.")
        return []

    def load_certification(self, selected_cert):
        """
        Carica i dati per la certificazione selezionata dalla cache o dal file Excel.
        """
        if self.blob_service_client and self.container_name:
            if 'blob_cache' in st.session_state and selected_cert in st.session_state.blob_cache['cert_databases']:
                self.df = st.session_state.blob_cache['cert_databases'][selected_cert].copy()
            else:
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
        else:
            self.df = pd.DataFrame()
        
        if not self.df.empty:
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
        if not self.blob_service_client or not self.container_name:
            return None
            
        # Crea una chiave univoca per questa immagine
        image_key = f"{selected_cert}_{topic}_{number}"
        
        # Verifica se l'immagine è già nella cache delle immagini
        if ('blob_cache' in st.session_state and 
            image_key in st.session_state.blob_cache['image_content_cache']):
            # Restituisci l'immagine dalla cache
            return io.BytesIO(st.session_state.blob_cache['image_content_cache'][image_key])
        
        # Verifica se abbiamo la mappa delle immagini in cache
        if ('blob_cache' in st.session_state and 
            selected_cert in st.session_state.blob_cache['cert_images'] and
            str(topic) in st.session_state.blob_cache['cert_images'][selected_cert] and
            int(number) in st.session_state.blob_cache['cert_images'][selected_cert][str(topic)]):
            
            # Ottieni il nome del blob dalla cache
            blob_name = st.session_state.blob_cache['cert_images'][selected_cert][str(topic)][int(number)]
            
            try:
                # Scarica il blob
                container_client = self.blob_service_client.get_container_client(self.container_name)
                blob_client = container_client.get_blob_client(blob_name)
                download_stream = blob_client.download_blob()
                content = download_stream.readall()
                
                # Salva nella cache delle immagini
                if 'blob_cache' in st.session_state:
                    st.session_state.blob_cache['image_content_cache'][image_key] = content
                
                return io.BytesIO(content)
            except Exception:
                import traceback
                traceback.print_exc()
                return None
        else:
            # Se non abbiamo la cache o l'immagine non è in cache, usa il metodo originale
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
                    
                    # Salva nella cache delle immagini
                    if 'blob_cache' in st.session_state:
                        st.session_state.blob_cache['image_content_cache'][image_key] = content
                    
                    return io.BytesIO(content)
                else:
                    return None
            except Exception:
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


def main():
    """
    Funzione principale che gestisce l'interfaccia utente e il flusso dell'applicazione.
    Utilizza Streamlit per creare l'interfaccia e gestire le interazioni dell'utente.
    """
    st.set_page_config(page_title="TRR Tool Certificazioni", layout="wide", page_icon=resource_path("static/icon.ico"))
    
    # Non richiamare load_config() qui, usa la variabile globale config
    
    if 'app' not in st.session_state:
        st.session_state.app = CertificationQuizApp(config)
    app = st.session_state.app
    
    # Inizializza la cache dei blob all'avvio
    if app.blob_service_client and app.container_name and 'blob_cache' not in st.session_state:
        with st.spinner("Inizializzazione della cache dei blob... Questo potrebbe richiedere qualche minuto."):
            cache_initialized = initialize_blob_cache(app)
            if not cache_initialized:
                st.error("Impossibile inizializzare la cache dei blob. L'applicazione potrebbe funzionare più lentamente.")

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

    # Aggiungi spazio verticale tra i controlli di selezione e il contenuto principale
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

    if st.session_state.show_guide:
        guide_content = load_markdown_content(config['guide_path'])
        st.markdown(guide_content, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([3,1], gap="large")
        
        with col1:
            if st.session_state.current_question is not None:
                # Mostra un messaggio durante il caricamento dell'immagine
                with st.spinner("Caricamento immagine..."):
                    image_path = app.find_image_file(cert, st.session_state.current_question['Topic'], st.session_state.current_question['Numero'])
                
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

                if pd.notna(st.session_state.current_question['Link']):
                    st.markdown(f"<a href='{st.session_state.current_question['Link']}' target='_blank'>Link alla domanda</a>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()