import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de Conexión centralizada

@st.cache_resource
def get_gsheet_client():
    # 1. SCOPES CORREGIDOS (Deben ser URLs completas a las APIs)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Obtenemos las secrets
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # Limpiamos la clave privada (Streamlit a veces escapa los saltos de línea)
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    # Generamos credenciales
    from google.oauth2.service_account import Credentials
    import gspread
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


# 2. Función de carga con caché
@st.cache_data(ttl=600)
def load_data(gid, sheet_id):
    client = get_gsheet_client() 
    sh = client.open_by_key(sheet_id)
    # Seleccionamos la hoja por su GID (id de la pestaña)
    worksheet = sh.get_worksheet_by_id(gid)
    return pd.DataFrame(worksheet.get_all_records())

# --- INICIO DE LA APP ---
sheet_id = "12plATZeI3STturtJtMog24m-e-WNGr1KcAOWQRuvVO0"

# Carga de datos
try:
    df_proyectos = load_data(0, sheet_id)
    df_materiales = load_data(1931749204, sheet_id)
    df_items = load_data(50989702, sheet_id)
    df_proy_detalle = load_data(1900275728, sheet_id)
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

st.title("Gestor de Materiales 2026")

# Menú lateral
modo = st.sidebar.radio("Navegación", ["Ver Consolidado", "Cargar Ítems"])

if modo == "Ver Consolidado":
    st.header("Consolidado de Proyecto")
    proyecto_sel = st.selectbox("Seleccionar Proyecto", df_proyectos['N_PROY'].unique())
    
    if st.button("Generar Listado"):
        id_p = df_proyectos.loc[df_proyectos['N_PROY'] == proyecto_sel, 'ID_PROY'].values[0]
        
        # Lógica de cálculo
        det = df_proy_detalle[df_proy_detalle['ID_PROY'] == id_p]
        if not det.empty:
            merged = det.merge(df_items, on='ID_ITEM')
            merged['CANT_TOTAL_MAT'] = merged['COMPUTO'] * merged['C_MAT']
            
            resumen = merged.groupby('ID_MAT')['CANT_TOTAL_MAT'].sum().reset_index()
            final = resumen.merge(df_materiales, on='ID_MAT')
            
            st.dataframe(final[['N_MAT', 'CANT_TOTAL_MAT', 'UNIDAD', 'COSTO_UNITARIO']])
        else:
            st.warning("Este proyecto no tiene ítems cargados.")

elif modo == "Cargar Ítems":
    st.header("Asignar Ítems")
    st.info("Formulario de carga listo para implementar.")
    
