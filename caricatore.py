import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from trasformatore import leggi_json, trasforma_dati_sonno_batteria, trasforma_attivita

def carica_su_sheets(kpi, lista_attivita):
    print("Connessione a Google Cloud...")
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    try:
        credenziali = ServiceAccountCredentials.from_json_keyfile_name('credenziali_google.json', scope)
        client = gspread.authorize(credenziali)
        db = client.open('Garmin_DB')
        
        # 1. Scrittura KPI su foglio 'Sonno'
        try:
            foglio_sonno = db.worksheet('Sonno')
        except gspread.exceptions.WorksheetNotFound:
            # Autocorrezione se il foglio si chiama ancora Foglio1
            foglio_sonno = db.sheet1
            foglio_sonno.update_title('Sonno')
            
        riga_sonno = [
            kpi.get("Data", "N/D"),
            kpi.get("Voto_Sonno", "N/D"),
            kpi.get("Qualita_Sonno", "N/D"),
            kpi.get("Ore_Totali", "N/D"),
            kpi.get("Body_Battery", "N/D")
        ]
        foglio_sonno.append_row(riga_sonno)
        print("-> Record Sonno e Batteria aggiunti.")
        
        # 2. Scrittura storico su foglio 'Attivita'
        try:
            foglio_att = db.worksheet('Attivita')
        except gspread.exceptions.WorksheetNotFound:
            print("ERRORE: Foglio 'Attivita' non trovato!")
            return
            
        # Pulizia del foglio e riscrittura massiva delle ultime 20 attività
        foglio_att.clear()
        foglio_att.append_row(["ID_Attivita", "Data_Ora", "Tipo", "Distanza_km", "Durata_min", "FC_Media", "Calorie"])
        
        dati_da_scrivere = []
        for act in lista_attivita:
            dati_da_scrivere.append([
                act["ID_Attivita"],
                act["Data_Ora"],
                act["Tipo"],
                act["Distanza_km"],
                act["Durata_min"],
                act["FC_Media"],
                act["Calorie"]
            ])
            
        if dati_da_scrivere:
            foglio_att.append_rows(dati_da_scrivere)
        print(f"-> {len(dati_da_scrivere)} Attività sincronizzate con successo.")
        
        print("\n[SUCCESSO GLOBALE] Data Warehouse aggiornato in Cloud.")
        
    except Exception as e:
        print(f"\n[ERRORE DI SISTEMA] Fallimento durante il caricamento: {e}")

if __name__ == "__main__":
    oggi = datetime.date.today()
    print(f"--- Avvio processo di Caricamento (Load) per la data {oggi} ---")
    
    f_sonno = os.path.join("dati_grezzi", f"sonno_{oggi}.json")
    f_batt = os.path.join("dati_grezzi", f"body_battery_{oggi}.json")
    f_att = os.path.join("dati_grezzi", f"attivita_{oggi}.json")
    
    kpi = trasforma_dati_sonno_batteria(leggi_json(f_sonno), leggi_json(f_batt))
    attivita = trasforma_attivita(leggi_json(f_att))
    
    if kpi:
        carica_su_sheets(kpi, attivita)