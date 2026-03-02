import os
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from google import genai

# 1. Caricamento Sicuro Credenziali e Token
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

# --- INIZIO AGGIUNTA: PIANO B PER IL CLOUD ---
if not gemini_key:
    try:
        import streamlit as st
        gemini_key = st.secrets["GEMINI_API_KEY"]
        telegram_token = st.secrets["TELEGRAM_TOKEN"]
        telegram_chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    except Exception:
        pass
# --- FINE AGGIUNTA ---

# Inizializzazione Client IA
client = genai.Client(api_key=gemini_key)

def recupera_ultimo_dato():
    """Connessione al Data Warehouse (Google Sheets) per estrarre l'ultimo record del SONNO."""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credenziali = ServiceAccountCredentials.from_json_keyfile_name('credenziali_google.json', scope)
    gc = gspread.authorize(credenziali)
    
    foglio = gc.open('Garmin_DB').sheet1
    records = foglio.get_all_records()
    
    if records:
        return records[-1]
    return None

def recupera_ultima_attivita():
    """Connessione al foglio ATTIVITA per estrarre l'ultimo workout sincronizzato."""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credenziali = ServiceAccountCredentials.from_json_keyfile_name('credenziali_google.json', scope)
    gc = gspread.authorize(credenziali)
    
    # Puntiamo esplicitamente al foglio delle attività
    foglio = gc.open('Garmin_DB').worksheet('Attivita')
    records = foglio.get_all_records()
    
    if records:
        return records[-1]
    return None

def genera_messaggio_coach(dati):
    """Elaborazione predittiva mattutina tramite LLM."""
    prompt = f"""
    Sei il Chief Athletic Officer di un professionista ambizioso. Il tuo cliente gestisce architetture dati complesse come analista funzionale SAP, studia per due master (MADMA ed EXECSM) e un MBA, porta avanti progetti visionari e la sua passione assoluta è la corsa.
    
    Oggi i suoi parametri fisiologici estratti dal Garmin sono:
    - Voto Sonno: {dati.get('Voto_Sonno')} su 100
    - Qualità: {dati.get('Qualita_Sonno')}
    
    REGOLE INGAGGIO:
    1. Valuta il recupero. Se alto, ordina di dominare l'asfalto. Se basso, prescrivi scarico.
    2. Tono da coach d'élite, ingegneristico, motivante, mindset manageriale.
    3. Conciso, dritto al punto, usa emoji.
    4. NO asterischi (**) o underscore (_). Solo testo semplice.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash', # Mantenuto riferimento modello (ottimizzato a 2.0)
        contents=prompt
    )
    return response.text

def genera_debriefing_post_allenamento(dati):
    """Analisi a consuntivo (Post-Workout) con approccio da Performance Manager."""
    prompt = f"""
    Analizza questo allenamento appena concluso per il tuo cliente (Analista SAP e Runner d'élite):
    - Tipo Attività: {dati.get('Tipo')}
    - Distanza: {dati.get('Distanza_km')} km
    - Durata: {dati.get('Durata_min')} min
    - FC Media: {dati.get('FC_Media')} bpm
    - Calorie: {dati.get('Calorie')}
    
    OBIETTIVO DEBRIEFING:
    1. Esegui un Load Assessment rapido: l'allenamento è stato efficiente rispetto ai battiti e alla distanza?
    2. Valuta l'impatto sul recupero aziendale/fisiologico.
    3. Feedback finale conciso e d'impatto (max 3 frasi).
    4. Tono: Manageriale, analitico, orientato al risultato.
    5. NO asterischi (**) o underscore (_). Solo testo semplice ed emoji.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def invia_notifica_telegram(messaggio):
    """Modulo di Delivery per push notification su smartphone."""
    print("Inizializzazione protocollo di rete verso i server Telegram...")
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    
    payload = {
       "chat_id": telegram_chat_id,
        "text": messaggio
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("[SUCCESSO] Notifica push consegnata!")
        else:
            print(f"[ERRORE DELIVERY] {response.text}")
    except Exception as e:
        print(f"[ECCEZIONE CRITICA] {e}")

if __name__ == "__main__":
    # Questo blocco rimane dedicato alla routine mattutina (CRON JOB)
    print("Esecuzione routine mattutina (Planning)...")
    ultimi_dati = recupera_ultimo_dato()
    
    if ultimi_dati:
        try:
            messaggio_generato = genera_messaggio_coach(ultimi_dati)
            url_dashboard = "https://francesco-digital-twin-garmin.streamlit.app/"
            messaggio_finale = f"{messaggio_generato}\n\n📡 Accesso SOC Dashboard:\n{url_dashboard}"
            
            print("=== PAYLOAD MESSAGGIO MATTUTINO ===")
            print(messaggio_finale)
            
            invia_notifica_telegram(messaggio_finale)
            
        except Exception as e:
            print(f"Errore: {e}")