import json
import os
import datetime

def leggi_json(percorso_file):
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def trasforma_dati_sonno_batteria(json_sonno, json_batteria):
    kpi = {
        "Data": str(datetime.date.today()),
        "Voto_Sonno": "N/D",
        "Qualita_Sonno": "N/D",
        "Ore_Totali": "N/D",
        "Body_Battery": "N/D"
    }
    
    if json_sonno:
        try:
            daily_sleep = json_sonno.get("dailySleepDTO", json_sonno)
            kpi["Qualita_Sonno"] = daily_sleep.get("sleepScoreFeedback", "N/D")
            kpi["Voto_Sonno"] = daily_sleep.get("sleepScores", {}).get("overall", {}).get("value", "N/D")
            secondi = daily_sleep.get("sleepTimeSeconds", 0)
            kpi["Ore_Totali"] = round(secondi / 3600, 2) if secondi else 0
        except Exception as e:
            print(f"Errore parsing sonno: {e}")

    # NUOVA LOGICA: Peschiamo l'ultimo valore puntuale della Body Battery
    if json_batteria and isinstance(json_batteria, list) and len(json_batteria) > 0:
        try:
            dati_bb = json_batteria[0]
            if "bodyBatteryValuesArray" in dati_bb:
                valori = dati_bb["bodyBatteryValuesArray"]
                # Filtriamo i valori nulli e prendiamo l'ultimo elemento valido dell'array
                valori_validi = [v[1] for v in valori if v[1] is not None]
                if valori_validi:
                    kpi["Body_Battery"] = valori_validi[-1] 
        except Exception as e:
            print(f"Errore parsing body battery: {e}")
            
    return kpi

    # Estrazione Body Battery
    if json_batteria and isinstance(json_batteria, list) and len(json_batteria) > 0:
        try:
            dati_bb = json_batteria[0]
            if "stat" in dati_bb:
                kpi["Body_Battery_Max"] = dati_bb["stat"].get("highestValue", "N/D")
                kpi["Body_Battery_Min"] = dati_bb["stat"].get("lowestValue", "N/D")
        except Exception as e:
            print(f"Errore parsing body battery: {e}")
            
    return kpi

def trasforma_attivita(json_attivita):
    lista_pulita = []
    if not json_attivita:
        return lista_pulita
        
    try:
        for act in json_attivita:
            # Calcolo conversioni per il Data Warehouse
            metri = act.get("distance", 0)
            km = round(metri / 1000, 2) if metri else 0
            
            secondi = act.get("duration", 0)
            minuti = round(secondi / 60, 2) if secondi else 0
            
            lista_pulita.append({
                "ID_Attivita": act.get("activityId", "N/D"),
                "Data_Ora": act.get("startTimeLocal", "N/D"),
                "Tipo": act.get("activityType", {}).get("typeKey", "Sconosciuto"),
                "Distanza_km": km,
                "Durata_min": minuti,
                "FC_Media": act.get("averageHR", 0),
                "Calorie": act.get("calories", 0)
            })
    except Exception as e:
        print(f"Errore parsing attività: {e}")
        
    return lista_pulita

if __name__ == "__main__":
    oggi = datetime.date.today()
    print(f"--- Avvio Trasformazione per la data {oggi} ---")
    
    f_sonno = os.path.join("dati_grezzi", f"sonno_{oggi}.json")
    f_batt = os.path.join("dati_grezzi", f"body_battery_{oggi}.json")
    f_att = os.path.join("dati_grezzi", f"attivita_{oggi}.json")
    
    kpi_giornalieri = trasforma_dati_sonno_batteria(leggi_json(f_sonno), leggi_json(f_batt))
    attivita_pulite = trasforma_attivita(leggi_json(f_att))
    
    print("\n[SUCCESSO] Dati Trasformati Correttamente!")
    print(f"KPI Generati: {kpi_giornalieri}")
    print(f"Attività elaborate: {len(attivita_pulite)}")