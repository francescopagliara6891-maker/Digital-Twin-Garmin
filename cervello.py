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

# Inizializzazione Client IA
client = genai.Client(api_key=gemini_key)

def recupera_ultimo_dato():
    """Connessione al Data Warehouse (Google Sheets) per estrarre l'ultimo record."""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credenziali = ServiceAccountCredentials.from_json_keyfile_name('credenziali_google.json', scope)
    gc = gspread.authorize(credenziali)
    
    foglio = gc.open('Garmin_DB').sheet1
    records = foglio.get_all_records()
    
    if records:
        return records[-1]
    return None

def genera_messaggio_coach(dati):
    """Elaborazione predittiva tramite LLM."""
    prompt = f"""
    Sei il Chief Athletic Officer di un professionista ambizioso. Il tuo cliente gestisce architetture dati complesse come analista funzionale SAP, studia per due master (MADMA ed EXECSM) e un MBA, porta avanti progetti visionari (come un'app web per lo studio e l'esercitazione su SQL, PYTHON e SAP Cloud Analytics), e la sua passione assoluta è la corsa.
    
    Oggi i suoi parametri fisiologici estratti dal Garmin sono:
    - Voto Sonno: {dati.get('Voto_Sonno')} su 100
    - Qualità: {dati.get('Qualita_Sonno')}
    
    Il suo focus atletico è il running: sessioni all'alba per macinare chilometri, migliorare il passo e dominare l'asfalto.
    
    REGOLE INGAGGIO:
    1. Valuta il suo livello di recupero. Se il Voto Sonno è alto, ordinargli di allacciare le scarpe da running e distruggere i chilometri oggi. Se il recupero è scarso, prescrivi una corsa di scarico o riposo strategico.
    2. Usa un tono da coach d'élite, deciso, ingegneristico ma motivante. Fai leva sul suo mindset da manager per spingerlo a performare.
    3. Sii conciso, dritto al punto. Nessun buongiorno sdolcinato. Usa emoji.
    4. IMPORTANTE: Genera solo testo semplice. NON usare MAI asterischi (**) o underscore (_) per formattare il testo. Usa solo testo normale e le emoji.
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
            print("[SUCCESSO] Notifica push consegnata al dispositivo target!")
        else:
            print(f"[ERRORE DELIVERY] I server Telegram hanno risposto con: {response.text}")
    except Exception as e:
        print(f"[ECCEZIONE CRITICA] Impossibile contattare Telegram: {e}")

if __name__ == "__main__":
    print("Recupero telemetria dal Data Warehouse (Google Sheets)...")
    ultimi_dati = recupera_ultimo_dato()
    
    if ultimi_dati:
        print(f"Dati rilevati: {ultimi_dati}")
        print("\nElaborazione strategia in corso (AI Engine)...\n")
        
        try:
            # 1. Genera il messaggio tramite l'IA
            messaggio_generato = genera_messaggio_coach(ultimi_dati)
            
            # --- INIEZIONE LINK DASHBOARD ---
            url_dashboard = "https://francesco-digital-twin-garmin.streamlit.app/"
            messaggio_finale = f"{messaggio_generato}\n\n📡 Accesso SOC Dashboard:\n{url_dashboard}"
            
            # 2. Mostra a schermo per log (con il fix per Windows)
            print("=== PAYLOAD MESSAGGIO ===")
            print(messaggio_finale.encode('utf-8', 'replace').decode('utf-8'))
            print("=========================\n")
            
            # 3. Spara la notifica sullo smartphone
            invia_notifica_telegram(messaggio_finale)
            
        except Exception as e:
            print(f"Errore critico durante l'elaborazione o l'invio: {e}")
    else:
        print("Nessun dato trovato nel database.")