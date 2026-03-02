import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
import json
import subprocess 
import datetime
import os
from cervello import genera_debriefing_post_allenamento 

# 1. Configurazione (DEVE ESSERE LA PRIMA ISTRUZIONE)
st.set_page_config(page_title="Digital Twin - F. Pagliara", page_icon="📈", layout="wide")

# 2. Connessione al Data Warehouse (Lettura)
@st.cache_data(ttl=600)
def carica_dati():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        # CONTROLLO PRIORITARIO: Esiste il file locale?
        if os.path.exists('credenziali_google.json'):
            credenziali = ServiceAccountCredentials.from_json_keyfile_name('credenziali_google.json', scope)
        # ALTRIMENTI: Cerca nei Secrets di Streamlit Cloud
        elif "GOOGLE_CREDENTIALS" in st.secrets:
            segreto = st.secrets["GOOGLE_CREDENTIALS"]
            credenziali_dict = json.loads(segreto) if isinstance(segreto, str) else dict(segreto)
            credenziali = ServiceAccountCredentials.from_json_keyfile_dict(credenziali_dict, scope)
        else:
            st.error("Nessun metodo di autenticazione trovato (file JSON o Secrets).")
            return pd.DataFrame(), pd.DataFrame()
            
        client = gspread.authorize(credenziali)
        db = client.open('Garmin_DB')
        
        df_sonno = pd.DataFrame(db.worksheet('Sonno').get_all_records())
        df_att = pd.DataFrame(db.worksheet('Attivita').get_all_records())
        return df_sonno, df_att
    except Exception as e:
        st.error(f"Errore di connessione globale: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Nuova funzione corazzata per scrivere i dati
def salva_dati_bilancia(peso, grasso_sotto, imc, massa_grassa, muscoli, acqua, proteine, metabolismo, grasso_visc, massa_ossea, muscolo_scheletrico, eta_corpo):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        # CONTROLLO 1: Locale
        if os.path.exists('credenziali_google.json'):
            credenziali = ServiceAccountCredentials.from_json_keyfile_name('credenziali_google.json', scope)
        # CONTROLLO 2: Cloud
        elif "GOOGLE_CREDENTIALS" in st.secrets:
            segreto = st.secrets["GOOGLE_CREDENTIALS"]
            credenziali_dict = json.loads(segreto) if isinstance(segreto, str) else dict(segreto)
            credenziali = ServiceAccountCredentials.from_json_keyfile_dict(credenziali_dict, scope)
        # CONTROLLO 3: Errore fatale
        else:
            st.error("ERRORE DI SISTEMA: Nessuna credenziale trovata per autorizzare la scrittura.")
            return False
        
        client = gspread.authorize(credenziali)
        foglio_bilancia = client.open('Garmin_DB').worksheet('Bilancia')
        
        nuova_riga = [datetime.date.today().strftime("%d/%m/%Y"), peso, grasso_sotto, imc, massa_grassa, muscoli, acqua, proteine, metabolismo, grasso_visc, massa_ossea, muscolo_scheletrico, eta_corpo]
        foglio_bilancia.append_row(nuova_riga)
        return True
        
    except Exception as e:
        # Questo ci dirà esattamente COSA sta bloccando il Cloud
        st.error(f"Errore tecnico durante il salvataggio dei dati bilancia: {str(e)}")
        return False

# Esecuzione
st.title("🏃‍♂️ Operations Center - Designed and Developed by Francesco Pagliara")
st.markdown("---")

df_sonno, df_att = carica_dati()

# --- DEFINIZIONE TAB ---
tab_dash, tab_gestione = st.tabs(["📊 Dashboard Analitica", "⚙️ Gestione & Bilancia"])

with tab_dash:
    if not df_sonno.empty and not df_att.empty:
        ultimo_sonno = df_sonno.iloc[-1]
        ultima_att = df_att.iloc[0] 
        
        st.subheader(f"📡 Telemetria Odierna ({ultimo_sonno['Data']})")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Voto Sonno", str(ultimo_sonno['Voto_Sonno']))
        col2.metric("Ore Totali", str(ultimo_sonno['Ore_Totali']))
        col4.metric("Qualità Recupero", str(ultimo_sonno['Qualita_Sonno']))
        
        with col3:
            bb_val = ultimo_sonno['Body_Battery']
            bb_num = int(bb_val) if str(bb_val).isdigit() else 0
            if bb_num > 0:
                fig_bb = go.Figure(go.Indicator(
                    mode = "gauge+number", value = bb_num,
                    title = {'text': "Body Battery", 'font': {'size': 14}},
                    gauge = {'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': "#0088ff"}}
                ))
                fig_bb.update_layout(height=150, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_bb, use_container_width=True)
            else:
                st.metric("Body Battery", "N/D")

        st.subheader("🔥 Ultima Attività Rilevata")
        col_att_1, col_att_2 = st.columns([1, 2])
        
        with col_att_1:
            st.info(f"**Tipo:** {str(ultima_att['Tipo']).upper().replace('_', ' ')}")
            st.write(f"📅 **Data/Ora:** {ultima_att['Data_Ora']}")
            st.write(f"📏 **Distanza:** {ultima_att['Distanza_km']} km")
            st.write(f"⏱️ **Durata:** {ultima_att['Durata_min']} min")
            st.write(f"❤️ **FC Media:** {ultima_att['FC_Media']} bpm")
            st.write(f"🔥 **Calorie:** {ultima_att['Calorie']} kcal")
            
        with col_att_2:
            df_corse = df_att[df_att['Tipo'].str.contains('running', case=False, na=False)].copy()
            if not df_corse.empty:
                df_corse = df_corse.sort_values(by="Data_Ora")
                fig_trend = px.line(df_corse, x="Data_Ora", y="Distanza_km", markers=True, 
                                    title="Trend Distanza Corse (km)", line_shape="spline",
                                    color_discrete_sequence=["#00ff00"])
                st.plotly_chart(fig_trend, use_container_width=True)
                
        st.markdown("---")
        st.subheader("🕸️ Bilanciamento Sistemico (Radar)")
        voto_sonno = int(ultimo_sonno['Voto_Sonno']) if str(ultimo_sonno['Voto_Sonno']).isdigit() else 0
        bb_radar = int(ultimo_sonno['Body_Battery']) if str(ultimo_sonno['Body_Battery']).isdigit() and int(ultimo_sonno['Body_Battery']) > 0 else 50
        fc_ultima = int(ultima_att['FC_Media']) if str(ultima_att['FC_Media']).isdigit() else 0
        carico_fisico = min((fc_ultima / 180) * 100, 100)
        
        categorie = ['Recupero Sonno', 'Energia (Body Battery)', 'Carico Fisico (Ultimo Workout)', 'Qualità Riposo']
        valori = [voto_sonno, bb_radar, carico_fisico, 85]
        
        fig_radar = go.Figure(go.Scatterpolar(r=valori, theta=categorie, fill='toself', name='Stato Attuale', line_color='#00e5ff'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        
        col_rad1, col_rad2 = st.columns([1,1])
        with col_rad1: st.plotly_chart(fig_radar, use_container_width=True)
        with col_rad2:
            st.write("### Interpretazione Radar")
            st.write("Analisi bilanciamento sistema.")
    else:
        st.warning("In attesa di dati dal Data Warehouse...")

with tab_gestione:
    st.header("⚙️ Operazioni Avanzate")
    st.subheader("🔄 Sincronizzazione Real-Time")
    
    if st.button("Lancia Sincronizzazione Garmin"):
        with st.spinner("Eseguendo estrattore.py..."):
            try:
                processo = subprocess.run(["python", "estrattore.py"], capture_output=True, text=True)
                if processo.returncode == 0:
                    st.success("✅ Database aggiornato!")
                    st.cache_data.clear()
                    
                    st.markdown("---")
                    st.subheader("🤖 AI Performance Debriefing")
                    _, df_nuovo_att = carica_dati()
                    if not df_nuovo_att.empty:
                        ultima_att_sync = df_nuovo_att.iloc[0]
                        with st.status("Gemini sta analizzando la performance...", expanded=True):
                            analisi = genera_debriefing_post_allenamento(ultima_att_sync)
                            st.write(analisi)
                else:
                    st.error(f"Errore script: {processo.stderr}")
            except Exception as e:
                st.error(f"Errore: {e}")

    st.markdown("---")
    st.subheader("⚖️ Log Bilancia Amazfit")
    # 3. INSERIMENTO DATI BILANCIA
    st.write("Inserisci i dati rilevati dalla bilancia Zepp. I valori predefiniti riflettono la tua ultima misurazione.")
    
    with st.form("bilancia_form", clear_on_submit=True):
        # Layout a 3 colonne per compattare i 12 campi
        c1, c2, c3 = st.columns(3)
        
        with c1:
            peso_in = st.number_input("Peso Corporeo (kg)", value=73.8, step=0.1)
            grasso_sotto_in = st.number_input("Grasso Sottocutaneo (%)", value=8.4, step=0.1)
            imc_in = st.number_input("IMC", value=21.4, step=0.1)
            massa_grassa_in = st.number_input("Massa Grassa (%)", value=11.9, step=0.1)
            
        with c2:
            muscoli_in = st.number_input("Muscoli (kg)", value=56.7, step=0.1)
            acqua_in = st.number_input("Acqua (%)", value=56.9, step=0.1)
            proteine_in = st.number_input("Proteine (%)", value=22.2, step=0.1)
            metabolismo_in = st.number_input("Metabolismo Basale (kcal)", value=1481, step=1)
            
        with c3:
            grasso_visc_in = st.number_input("Grasso Viscerale", value=7, step=1)
            massa_ossea_in = st.number_input("Massa Ossea (kg)", value=3.1, step=0.1)
            muscolo_scheletrico_in = st.number_input("Muscolatura Scheletrica (kg)", value=29.2, step=0.1)
            eta_corpo_in = st.number_input("Età del Corpo", value=35, step=1)
        
        if st.form_submit_button("Registra Dati Biometrici"):
            # Passiamo tutti e 12 i parametri alla funzione
            if salva_dati_bilancia(peso_in, grasso_sotto_in, imc_in, massa_grassa_in, muscoli_in, acqua_in, proteine_in, metabolismo_in, grasso_visc_in, massa_ossea_in, muscolo_scheletrico_in, eta_corpo_in):
                st.balloons()
                st.success("Dati biometrici registrati e allineati nel Data Warehouse!")