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
    with open(resource_path(file_path), 'r', encoding='utf-8') as file:
        content = file.read()
        # Converti il markdown in HTML con i tag <br> per le nuove righe
        html = markdown.markdown(content, extensions=['nl2br', 'toc'])
        return html


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


    def get_available_certifications(self):
        """
        Recupera l'elenco delle certificazioni disponibili, sia da una fonte locale che remota.
        """
        data_dir = resource_path(self.data_path)
        if data_dir.startswith(('http://', 'https://')):
            return self._get_remote_certifications(data_dir)
        else:
            return self._get_local_certifications(data_dir)


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
            print(f"Errore nel recupero delle certificazioni remote: {e}")
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
        file_path = resource_path(os.path.join(self.data_path, selected_cert, "database.xlsx"))
        if file_path.startswith(('http://', 'https://')):
            try:
                self.df = pd.read_excel(file_path)
            except Exception as e:
                print(f"Errore nel caricamento del database remoto: {e}")
                self.df = pd.DataFrame()
        else:
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
        image_dir = resource_path(os.path.join(self.data_path, selected_cert, "Domande", f"Topic{topic}"))
        if image_dir.startswith(('http://', 'https://')):
            return self._find_remote_image(image_dir, number)
        else:
            return self._find_local_image(image_dir, number)


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
                    return urljoin(url, href)
            return None
        except requests.RequestException as e:
            print(f"Errore nel recupero dell'immagine remota: {e}")
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

    st.title("TRR Tool Certificazioni")

    col1, col2 = st.columns([3,1], gap="large")

    with col1:
        col1a, col1b = st.columns(2)
        with col1a:
            cert = st.selectbox("Seleziona Certificazione:", app.get_available_certifications())
        
        if cert:
            if cert != st.session_state.current_cert:
                app.reset_score()
                st.session_state.current_cert = cert
                st.session_state.current_topic = None
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
            guide_button_text = "Chiudi la Guida" if st.session_state.show_guide else "Guida all'utilizzo"
            if st.button(guide_button_text, use_container_width=True, key="guide_button"):
                st.session_state.show_guide = not st.session_state.show_guide
                st.rerun()
        with col2b:
            st.button("Chiedi all'Agent AI", on_click=lambda: webbrowser.open_new(config['ai_agent_url']), use_container_width=True)

    if st.session_state.show_guide:
        guide_content = load_markdown_content(config['guide_path'])
        st.markdown(guide_content, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([3,1], gap="large")
        
        with col1:
            if st.session_state.current_question is not None:
                image_path = app.find_image_file(cert, st.session_state.current_question['Topic'], st.session_state.current_question['Numero'])
                if image_path:
                    image = Image.open(image_path)
                    
                    # Centra l'immagine usando le colonne di Streamlit
                    left, center, right = st.columns([1,5,1])
                    with center:
                        st.image(image, use_container_width=True)
                else:
                    st.write("Immagine non trovata")

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
                st.write(f"Ancora dubbi? [Chiedi all'Agent AI]({config['ai_agent_url']})")

                if pd.notna(st.session_state.current_question['Link']):
                    st.markdown(f"[Link alla domanda]({st.session_state.current_question['Link']})")

if __name__ == "__main__":
    main()