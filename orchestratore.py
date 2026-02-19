import subprocess
import time
import datetime

def esegui_modulo(nome_script):
    print(f"\n---> Esecuzione Modulo: {nome_script} <---")
    # Lancia lo script come se lo scrivessi tu nel terminale
    risultato = subprocess.run(["python", nome_script], capture_output=True, text=True)
    
    # Stampa a schermo l'output del modulo
    print(risultato.stdout)
    
    if risultato.returncode != 0:
        print(f"[ERRORE CRITICO] Il modulo {nome_script} ha fallito:")
        print(risultato.stderr)
        return False
    return True

if __name__ == "__main__":
    oggi = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"==================================================")
    print(f" AVVIO BATCH: DIGITAL TWIN PIPELINE")
    print(f" TIMESTAMP: {oggi}")
    print(f"==================================================")

    # La sequenza esatta del nostro processo ETL + AI
    moduli = [
        "estrattore.py",     # Extract
        "trasformatore.py",  # Transform
        "caricatore.py",     # Load
        "cervello.py"        # AI & Delivery
    ]

    for modulo in moduli:
        successo = esegui_modulo(modulo)
        if not successo:
            print("\n[BLOCCO SISTEMA] Interruzione catena per errore.")
            break
        time.sleep(2) # Pausa tattica di 2 secondi tra un processo e l'altro

    print(f"\n==================================================")
    print(f" CICLO BATCH COMPLETATO CON SUCCESSO")
    print(f"==================================================")