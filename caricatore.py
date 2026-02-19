import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Importiamo le logiche dal nostro nodo di Trasformazione
from trasformatore import leggi_json, trasforma_dati_sonno

def carica_su_sheets(dati_kpi):
    """Autentica il bot e scrive il record su Google Sheets."""
    print("Inizializzazione protocollo IAM e connessione a Google Cloud...")
    
    # 1. Definizione dello scope (i permessi dell'API)
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        # 2. Autenticazione tramite la chiave cifrata
        credenziali = ServiceAccountCredentials.from_json_keyfile_name('credenziali_google.json', scope)
        client = gspread.authorize(credenziali)
        
        # 3. Aggancio al database (Foglio Google)
        print("Connessione al Data Warehouse 'Garmin_DB'...")
        foglio = client.open('Garmin_DB').sheet1
        
        # 4. Mappatura del tracciato record (deve corrispondere alle tue colonne)
        riga = [
            dati_kpi.get("Data", "N/D"),
            dati_kpi.get("Voto_Sonno", "N/D"),
            dati_kpi.get("Qualita_Sonno", "N/D"),
            dati_kpi.get("Ore_Totali", "N/D")
        ]
        
        # 5. Commit della transazione (Scrittura)
        print(f"Commit del record in corso: {riga}")
        foglio.append_row(riga)
        print("\n[SUCCESSO GLOBALE] Transazione completata! Il tuo Gemello Digitale è aggiornato in Cloud.")
        
    except Exception as e:
        print(f"\n[ERRORE DI SISTEMA] Fallimento durante il caricamento: {e}")

if __name__ == "__main__":
    oggi = datetime.date.today()
    print(f"--- Avvio processo di Caricamento (Load) per la data {oggi} ---")
    
    # Recuperiamo il file generato nello staging
    file_sonno = os.path.join("dati_grezzi", f"sonno_{oggi}.json")
    json_sonno = leggi_json(file_sonno)
    
    if json_sonno:
        # Trasformiamo i dati al volo
        kpi = trasforma_dati_sonno(json_sonno)
        
        # Se abbiamo i KPI, lanciamo il caricamento
        if kpi:
            carica_su_sheets(kpi)