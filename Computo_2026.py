import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de página
st.set_page_config(page_title="Gestor de Materiales 2026", layout="wide")

# 2. Conexión Silenciosa
@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets.connections.gsheets)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

client = get_client()
url_real = "https://docs.google.com/spreadsheets/d/12plATZeI3STturtJtMog24m-e-WNGr1KcAOWQRuvVO0/"
sh = client.open_by_url(url_real)

# 3. Funciones de carga con caché (usando nombres corregidos)
@st.cache_data(ttl=600)
def load_data(worksheet_name):
    try:
        ws = sh.worksheet(worksheet_name)
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

# Carga inicial
df_proyectos = load_data("PROYECTOS")
df_materiales = load_data("M_MATERIALES")
df_items = load_data("ITEMS")
df_proy_detalle = load_data("PROY_DETALLE")

# Previsión de tabla vacía
if df_proyectos.empty:
    df_proyectos = pd.DataFrame(columns=['ID_PROY', 'NOMBRE', 'CLIENTE'])

# --- INTERFAZ ---
st.title("🏗️ Gestor de Materiales 2026")

# UN SOLO MENÚ DE NAVEGACIÓN
modo = st.sidebar.selectbox("Seleccionar Acción", 
    ["📊 Ver Consolidado", "🏗️ Cargar Ítems", "➕ Crear Nuevo Proyecto"])

# 3. SECCIÓN: VER CONSOLIDADO
elif modo == "📊 Ver Consolidado":
    st.header("Consolidado de Proyecto")
    
    if df_proyectos.empty:
        st.info("Aún no has creado ningún proyecto. Ve a la sección '➕ Crear Nuevo Proyecto'.")
    else:
        # El selector y el botón aparecen ANTES de validar los datos detalle
        proyecto_sel = st.selectbox("Seleccionar Proyecto", df_proyectos['NOMBRE'].unique())
        
        if st.button("🔍 Generar Listado"):
            id_p = df_proyectos.loc[df_proyectos['NOMBRE'] == proyecto_sel, 'ID_PROY'].values[0]
            
            # Buscamos si hay algo en detalle para ese ID específico
            if not df_proy_detalle.empty:
                det = df_proy_detalle[df_proy_detalle['ID_PROY'] == id_p].copy()
                
                if not det.empty:
                    # Lógica de cálculo (Merge y sumatorias)
                    merged = det.merge(df_items, on='ID_ITEM')
                    merged['CANT_TOTAL_MAT'] = merged['COMPUTO'] * merged['C_MAT']
                    resumen = merged.groupby('ID_MAT')['CANT_TOTAL_MAT'].sum().reset_index()
                    final = resumen.merge(df_materiales, on='ID_MAT')
                    
                    st.subheader(f"Lista de Materiales - {proyecto_sel}")
                    st.dataframe(final[['N_MAT', 'CANT_TOTAL_MAT', 'UNIDAD', 'COSTO_UNITARIO']], use_container_width=True)
                else:
                    st.warning(f"El proyecto '{proyecto_sel}' aún no tiene ítems cargados. Ve a '🏗️ Cargar Ítems'.")
            else:
                st.warning("La tabla de detalles está totalmente vacía. Empieza cargando ítems a tus proyectos.")
