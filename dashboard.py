import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
import json

# 1. Configurazione
st.set_page_config(page_title="Digital Twin - F. Pagliara", page_icon="📈", layout="wide")
st.title("🏃‍♂️ Operations Center - Designed and Developed by Francesco Pagliara")
st.markdown("---")

# 2. Connessione al Data Warehouse
@st.cache_data(ttl=600)
def carica_dati():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        if "GOOGLE_CREDENTIALS" in st.secrets:
            # SIAMO IN CLOUD
            try:
                segreto = st.secrets["GOOGLE_CREDENTIALS"]
                # Streamlit a volte converte in automatico il TOML in dizionario
                if isinstance(segreto, str):
                    credenziali_dict = json.loads(segreto)
                else:
                    credenziali_dict = dict(segreto)
                credenziali = ServiceAccountCredentials.from_json_keyfile_dict(credenziali_dict, scope)
            except Exception as ex_cloud:
                st.error(f"Errore di parsing dei Secrets in Cloud: {ex_cloud}")
                return pd.DataFrame(), pd.DataFrame()
        else:
            # SIAMO SUL PC LOCALE
            credenziali = ServiceAccountCredentials.from_json_keyfile_name('credenziali_google.json', scope)
            
        client = gspread.authorize(credenziali)
        db = client.open('Garmin_DB')
        
        df_sonno = pd.DataFrame(db.worksheet('Sonno').get_all_records())
        df_att = pd.DataFrame(db.worksheet('Attivita').get_all_records())
        return df_sonno, df_att
    except Exception as e:
        st.error(f"Errore di connessione globale: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_sonno, df_att = carica_dati()

if not df_sonno.empty and not df_att.empty:
    ultimo_sonno = df_sonno.iloc[-1]
    ultima_att = df_att.iloc[0] # La prima riga è la più recente
    
    # --- LIVELLO 1: SNAPSHOT ISTANTANEO ---
    st.subheader(f"📡 Telemetria Odierna ({ultimo_sonno['Data']})")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Voto Sonno", str(ultimo_sonno['Voto_Sonno']))
    col2.metric("Ore Totali", str(ultimo_sonno['Ore_Totali']))
    col4.metric("Qualità Recupero", str(ultimo_sonno['Qualita_Sonno']))
    
    # Donut Chart per Body Battery nella colonna 3
    with col3:
        bb_val = ultimo_sonno['Body_Battery']
        bb_num = int(bb_val) if str(bb_val).isdigit() else 0
        
        if bb_num > 0:
            fig_bb = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = bb_num,
                title = {'text': "Body Battery", 'font': {'size': 14}},
                gauge = {
                    'axis': {'range': [0, 100], 'visible': False},
                    'bar': {'color': "#0088ff"},
                    'shape': "angular"
                }
            ))
            fig_bb.update_layout(height=150, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_bb, use_container_width=True)
        else:
            st.metric("Body Battery", "N/D")

    # --- LIVELLO 2: ANALISI ULTIMA ATTIVITÀ ---
    st.subheader("🔥 Ultima Attività Rilevata")
    
    # Layout a due colonne: Dati a sinistra, Grafico a destra
    col_att_1, col_att_2 = st.columns([1, 2])
    
    with col_att_1:
        st.info(f"**Tipo:** {str(ultima_att['Tipo']).upper().replace('_', ' ')}")
        st.write(f"📅 **Data/Ora:** {ultima_att['Data_Ora']}")
        st.write(f"📏 **Distanza:** {ultima_att['Distanza_km']} km")
        st.write(f"⏱️ **Durata:** {ultima_att['Durata_min']} min")
        st.write(f"❤️ **FC Media:** {ultima_att['FC_Media']} bpm")
        st.write(f"🔥 **Calorie:** {ultima_att['Calorie']} kcal")
        
    with col_att_2:
        # Filtriamo solo le corse per fare un grafico di trend sensato
        df_corse = df_att[df_att['Tipo'].str.contains('running', case=False, na=False)].copy()
        if not df_corse.empty:
            # Ordiniamo cronologicamente
            df_corse = df_corse.sort_values(by="Data_Ora")
            fig_trend = px.line(df_corse, x="Data_Ora", y="Distanza_km", markers=True, 
                                title="Trend Distanza Corse (km)", line_shape="spline",
                                color_discrete_sequence=["#00ff00"])
            st.plotly_chart(fig_trend, use_container_width=True)
            
    st.markdown("---")
    
    # --- LIVELLO 3: RADAR CHART (Equilibrio) ---
    st.subheader("🕸️ Bilanciamento Sistemico (Radar)")
    
    # Normalizziamo alcuni valori per il radar (scala 0-100)
    voto_sonno = int(ultimo_sonno['Voto_Sonno']) if str(ultimo_sonno['Voto_Sonno']).isdigit() else 0
    bb_radar = bb_val if bb_val > 0 else 50 # Default se assente
    
    # Se l'ultima attività è stata tosta (es. fc > 130), lo stress fisico è più alto
    fc_ultima = int(ultima_att['FC_Media']) if str(ultima_att['FC_Media']).isdigit() else 0
    carico_fisico = min((fc_ultima / 180) * 100, 100) # Stimiamo un carico su base 100
    
    categorie = ['Recupero Sonno', 'Energia (Body Battery)', 'Carico Fisico (Ultimo Workout)', 'Qualità Riposo']
    valori = [voto_sonno, bb_radar, carico_fisico, 85] # 85 placeholder qualità
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=valori,
        theta=categorie,
        fill='toself',
        name='Stato Attuale',
        line_color='#00e5ff'  # BLU ELETTRICO
    ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    
    col_rad1, col_rad2 = st.columns([1,1])
    with col_rad1:
        st.plotly_chart(fig_radar, use_container_width=True)
    with col_rad2:
        st.write("### Interpretazione Radar")
        st.write("Questo grafico valuta il bilanciamento tra l'input (il tuo recupero) e l'output (il carico fisico sostenuto).")
        st.write("Se l'area si sbilancia troppo verso il 'Carico Fisico' mentre il 'Recupero Sonno' è basso, il sistema ti segnalerà un rischio di overtraining.")
else:
    st.warning("In attesa di dati dal Data Warehouse...")