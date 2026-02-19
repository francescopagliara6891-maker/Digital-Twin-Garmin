import json
import os
import datetime

def leggi_json(percorso_file):
    """Apre e legge un file JSON salvato in locale."""
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERRORE] Il file {percorso_file} non esiste. Hai lanciato prima l'estrattore?")
        return None

def trasforma_dati_sonno(dati_grezzi):
    """Mappa ed estrae i KPI strategici dal JSON del sonno."""
    if not dati_grezzi:
        return None
        
    # Inizializziamo un dizionario pulito per il nostro Data Warehouse
    kpi_sonno = {
        "Data": str(datetime.date.today()),
        "Voto_Sonno": None,
        "Qualita_Sonno": None,
        "Ore_Totali": None
    }
    
    # Navighiamo nel JSON in modo sicuro usando il metodo .get()
    # Adattiamo la ricerca alla struttura tipica del payload Garmin
    try:
        # Peschiamo i dati dal nodo principale (potrebbe variare leggermente, ma questo è lo standard)
        daily_sleep = dati_grezzi.get("dailySleepDTO", dati_grezzi)
        
        # Estraiamo i valori esatti che hai individuato tu!
        feedback = daily_sleep.get("sleepScoreFeedback", "N/D")
        
        # Il voto è dentro il dizionario "sleepScores", poi dentro "overall", poi "value"
        sleep_scores = daily_sleep.get("sleepScores", {})
        overall = sleep_scores.get("overall", {})
        voto = overall.get("value", "N/D")
        
        # Calcoliamo le ore totali (Garmin le dà in secondi)
        secondi_totali = daily_sleep.get("sleepTimeSeconds", 0)
        ore_totali = round(secondi_totali / 3600, 2) if secondi_totali else 0
        
        # Popoliamo il nostro record pulito
        kpi_sonno["Voto_Sonno"] = voto
        kpi_sonno["Qualita_Sonno"] = feedback
        kpi_sonno["Ore_Totali"] = ore_totali
        
        return kpi_sonno
        
    except Exception as e:
        print(f"Errore durante il parsing del sonno: {e}")
        return None

if __name__ == "__main__":
    oggi = datetime.date.today()
    print(f"--- Avvio processo di Trasformazione (Data Mapping) per la data {oggi} ---")
    
    # 1. Definiamo i percorsi dei file grezzi
    file_sonno = os.path.join("dati_grezzi", f"sonno_{oggi}.json")
    
    # 2. Leggiamo il dato grezzo
    json_sonno = leggi_json(file_sonno)
    
    # 3. Trasformiamo il dato
    if json_sonno:
        kpi_puliti = trasforma_dati_sonno(json_sonno)
        print("\n[SUCCESSO] Dati Trasformati Correttamente!")
        print("-" * 40)
        for chiave, valore in kpi_puliti.items():
            print(f"{chiave.ljust(15)} : {valore}")
        print("-" * 40)