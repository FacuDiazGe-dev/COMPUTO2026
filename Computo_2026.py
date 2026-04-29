
    
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# AÑADE ESTO PARA DIAGNÓSTICO
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    st.write(f"Intentando conectar con: {st.secrets.connections.gsheets['client_email']}")
else:
    st.error("No se detectó la configuración [connections.gsheets] en los Secrets.")

# 1. Configuración de página (SIEMPRE PRIMERO)
st.set_page_config(page_title="Gestor de Materiales 2026", layout="wide")

st.title("Gestor de Materiales 2026")

# 2. URL de tu planilla
sheet_url = "https://google.com"

# 3. Bloque de conexión manual
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    # Creamos una copia para poder editar la private_key
    creds_info = dict(st.secrets["connections"]["gsheets"])
    
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Intentamos abrir el archivo
    sh = client.open_by_url(sheet_url)
    st.sidebar.success(f"Conectado como: {creds_info['client_email']}")
    
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

# 4. Funciones de carga usando el 'client' manual
@st.cache_data(ttl=600)
def load_manual_data(worksheet_name):
    worksheet = sh.worksheet(worksheet_name)
    return pd.DataFrame(worksheet.get_all_records())

# Carga de datos
df_proyectos = load_manual_data("PROYECTOS")
df_materiales = load_manual_data("MATERIALES")
df_items = load_manual_data("ITEMS")
df_proy_detalle = load_manual_data("DETALLE_PROY")

# --- NAVEGACIÓN ---
modo = st.sidebar.radio("Navegación", ["Ver Consolidado", "Cargar Ítems"])

if modo == "Ver Consolidado":
    st.header("Consolidado de Proyecto")
    proyecto_sel = st.selectbox("Seleccionar Proyecto", df_proyectos['N_PROY'].unique())
    
    if st.button("Generar Listado"):
        id_p = df_proyectos.loc[df_proyectos['N_PROY'] == proyecto_sel, 'ID_PROY'].values[0]
        det = df_proy_detalle[df_proy_detalle['ID_PROY'] == id_p].copy()
        
        if not det.empty:
            merged = det.merge(df_items, on='ID_ITEM')
            merged['CANT_TOTAL_MAT'] = merged['COMPUTO'] * merged['C_MAT']
            resumen = merged.groupby('ID_MAT')['CANT_TOTAL_MAT'].sum().reset_index()
            final = resumen.merge(df_materiales, on='ID_MAT')
            st.dataframe(final[['N_MAT', 'CANT_TOTAL_MAT', 'UNIDAD', 'COSTO_UNITARIO']], use_container_width=True)
        else:
            st.warning("No hay ítems cargados para este proyecto.")

elif modo == "Cargar Ítems":
    st.header("Asignar Nuevo Ítem")
    with st.form("form_carga"):
        p_sel = st.selectbox("Proyecto", df_proyectos['N_PROY'].unique())
        i_sel = st.selectbox("Ítem", df_items['N_ITEM'].unique())
        cant = st.number_input("Cómputo", min_value=0.0, step=0.1)
        
        if st.form_submit_button("Guardar en Sheet"):
            id_p = df_proyectos.loc[df_proyectos['N_PROY'] == p_sel, 'ID_PROY'].values[0]
            id_i = df_items.loc[df_items['N_ITEM'] == i_sel, 'ID_ITEM'].values[0]
            
            # gspread permite append_row directamente, es más eficiente
            nueva_fila = [int(id_p), int(id_i), cant]
            sh.worksheet("DETALLE_PROY").append_row(nueva_fila)
            
            st.success("¡Guardado exitosamente!")
            st.cache_data.clear()
    
