import os
import json
import datetime
from dotenv import load_dotenv
from garminconnect import Garmin

# 1. Caricamento sicuro delle credenziali
load_dotenv()
email = os.getenv("GARMIN_EMAIL")
password = os.getenv("GARMIN_PASSWORD")

def init_garmin():
    print("Tentativo di login in corso...")
    try:
        client = Garmin(email, password)
        client.login()
        print("Login effettuato con successo!\n")
        return client
    except Exception as e:
        print(f"Errore di autenticazione: {e}")
        return None

def salva_file_json(dati, nome_file):
    # 2. Creazione automatica della cartella di staging
    cartella_staging = "dati_grezzi"
    if not os.path.exists(cartella_staging):
        os.makedirs(cartella_staging)
        print(f"[SYSTEM] Cartella '{cartella_staging}' creata con successo nel progetto.")
        
    percorso_completo = os.path.join(cartella_staging, nome_file)
    
    # 3. Scrittura fisica del file sul disco
    with open(percorso_completo, 'w', encoding='utf-8') as f:
        json.dump(dati, f, ensure_ascii=False, indent=4)
        
    print(f"--> File salvato correttamente in: {percorso_completo}")

if __name__ == "__main__":
    garmin_client = init_garmin()
    
    if garmin_client:
        oggi = datetime.date.today()
        print(f"--- Avvio estrazione dati per la data: {oggi} ---")
        
        try:
            print("\nEstrazione metriche sonno...")
            sleep_data = garmin_client.get_sleep_data(oggi.isoformat())
            salva_file_json(sleep_data, f"sonno_{oggi}.json")
            
            print("\nEstrazione Body Battery...")
            body_battery = garmin_client.get_body_battery(oggi.isoformat())
            salva_file_json(body_battery, f"body_battery_{oggi}.json")
            
            print("\n[SUCCESS] Processo completato! Controlla la cartella del progetto.")
            
        except Exception as e:
            print(f"Errore durante il download dei dati: {e}")