import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de Conexión (Asegúrate de tener esto en Secrets)
def get_gsheet_client():
    scope = ["https://googleapis.com"]
    # En Streamlit Cloud, pega el JSON en la sección Secrets
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# 2. Definición de funciones ANTES de usarlas
def load_data(gid, sheet_id, client):
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet_by_id(gid)
    return pd.DataFrame(worksheet.get_all_records())

# 3. Caching

@st.cache_resource
def get_gsheet_client():
    scope = ["https://googleapis.com", "https://googleapis.com"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# 4. Función de carga ajustada (quitamos 'client' de los argumentos)
@st.cache_data(ttl=600)
def load_data(gid, sheet_id):
    # Obtenemos el cliente aquí adentro
    client = get_gsheet_client() 
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet_by_id(gid)
    return pd.DataFrame(worksheet.get_all_records())

# --- INICIO DE LA APP ---

sheet_id = "12plATZeI3STturtJtMog24m-e-WNGr1KcAOWQRuvVO0"

# Carga de datos inicial
df_proyectos = load_data(0, sheet_id, client)
df_materiales = load_data(1931749204, sheet_id, client)
df_items = load_data(50989702, sheet_id, client)
df_proy_detalle = load_data(1900275728, sheet_id, client)

st.title("Gestor de Materiales 2026")

# Menú lateral
modo = st.sidebar.radio("Navegación", ["Ver Consolidado", "Cargar Ítems"])

if modo == "Ver Consolidado":
    st.header("Consolidado de Proyecto")
    proyecto_sel = st.selectbox("Seleccionar Proyecto", df_proyectos['N_PROY'].unique())
    
    if st.button("Generar Listado"):
        id_p = df_proyectos.loc[df_proyectos['N_PROY'] == proyecto_sel, 'ID_PROY'].values[0]
        
        # Filtrar detalle y calcular
        det = df_proy_detalle[df_proy_detalle['ID_PROY'] == id_p]
        merged = det.merge(df_items, on='ID_ITEM')
        merged['CANT_TOTAL_MAT'] = merged['COMPUTO'] * merged['C_MAT']
        
        resumen = merged.groupby('ID_MAT')['CANT_TOTAL_MAT'].sum().reset_index()
        final = resumen.merge(df_materiales, on='ID_MAT')
        
        st.dataframe(final[['N_MAT', 'CANT_TOTAL_MAT', 'UNIDAD', 'COSTO_UNITARIO']])

elif modo == "Cargar Ítems":
    st.header("Asignar Ítems")
    # Aquí iría el formulario de carga que vimos antes
    st.info("Formulario de carga listo para implementar.")
    
