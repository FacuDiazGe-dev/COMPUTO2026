import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. CONFIGURACIÓN CENTRALIZADA
st.set_page_config(page_title="Gestor Materiales 2026", layout="wide")

# Centralizamos la URL (Asegúrate de que este sea el ID correcto de tu Sheet)
SHEET_URL = "https://google.com"

@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets.connections.gsheets)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    scopes = ["https://googleapis.com", "https://googleapis.com"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# Inicializamos cliente y acceso al archivo
client = get_client()
sh = client.open_by_url(SHEET_URL)

# 2. FUNCIÓN DE CARGA POR GID
@st.cache_data(ttl=60)
def load_data(gid):
    try:
        ws = sh.get_worksheet_by_id(gid)
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

# --- NAVEGACIÓN ---
st.sidebar.title("🛠️ Menú de Gestión")
opcion = st.sidebar.selectbox("Seleccione una opción", [
    "📁 Ver Proyectos", 
    "➕ Crear Proyecto", 
    "🏗️ Gestionar Ítems", 
    "📦 Gestionar Materiales",
    "📊 Consolidado Final"
])

st.title(f"{opcion}")

# --- MÓDULO 1: VER PROYECTOS ---
if opcion == "📁 Ver Proyectos":
    df_proy = load_data(0) # GID de Proyectos
    if df_proy.empty:
        st.info("No hay proyectos registrados.")
    else:
        st.subheader("Listado Actual de Proyectos")
        st.dataframe(df_proy, use_container_width=True, hide_index=True)

# --- MÓDULO 2: CREAR PROYECTO ---
elif opcion == "➕ Crear Proyecto":
    st.subheader("Registrar Nuevo Proyecto en la Base")
    df_proy = load_data(0)
    
    with st.form("form_nuevo_proy", clear_on_submit=True):
        nombre = st.text_input("Nombre del Proyecto")
        cliente = st.text_input("Cliente / Empresa")
        
        if st.form_submit_button("💾 Guardar en Google Sheets"):
            if nombre:
                # Lógica de ID: máximo actual + 1
                nuevo_id = 1 if df_proy.empty else int(df_proy['ID_PROY'].max()) + 1
                nueva_fila = [nuevo_id, nombre, cliente]
                
                try:
                    sh.get_worksheet_by_id(0).append_row(nueva_fila)
                    st.success(f"✅ Proyecto '{nombre}' creado con ID {nuevo_id}")
                    st.cache_data.clear() # Limpiamos para que aparezca en 'Ver Proyectos'
                except Exception as e:
                    st.error(f"Error al escribir: {e}")
            else:
                st.warning("El nombre es obligatorio.")

# --- MÓDULO 3: GESTIONAR ÍTEMS ---
elif opcion == "🏗️ Gestionar Ítems":
    st.subheader("Base de Datos de Ítems de Obra")
    df_items = load_data(50989702)
    st.dataframe(df_items, use_container_width=True)

# --- MÓDULO 4: GESTIONAR MATERIALES ---
elif opcion == "📦 Gestionar Materiales":
    st.subheader("Catálogo de Materiales")
    df_mat = load_data(1931749204)
    st.dataframe(df_mat, use_container_width=True)

# --- MÓDULO 5: CONSOLIDADO FINAL ---
elif opcion == "📊 Consolidado Final":
    st.info("Aquí cargaremos la lógica de cálculo por proyecto próximamente.")
