import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de página
st.set_page_config(page_title="Gestor Materiales 2026", layout="wide")

# URL EXACTA SOLICITADA
url_real = "https://docs.google.com/spreadsheets/d/12plATZeI3STturtJtMog24m-e-WNGr1KcAOWQRuvVO0/"

# 2. Conexión Silenciosa
@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets.connections.gsheets)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    scopes = [
        "https://googleapis.com",
        "https://googleapis.com"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# Inicialización de cliente y archivo
client = get_client()
sh = client.open_by_url(url_real)

# 3. Función de carga por GID
@st.cache_data(ttl=60)
def load_data(gid):
    try:
        ws = sh.get_worksheet_by_id(gid)
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

# --- NAVEGACIÓN (BOTONERA) ---
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
    df_proy = load_data(0) # GID Proyectos
    if df_proy.empty:
        st.info("La tabla de proyectos está vacía.")
    else:
        st.subheader("Listado Actual")
        st.dataframe(df_proy, use_container_width=True, hide_index=True)

# --- MÓDULO 2: CREAR PROYECTO ---
elif opcion == "➕ Crear Proyecto":
    st.subheader("Registrar Nuevo Proyecto")
    df_proy = load_data(0)
    
    with st.form("form_nuevo_proy", clear_on_submit=True):
        nombre = st.text_input("Nombre del Proyecto")
        cliente = st.text_input("Cliente / Empresa")
        if st.form_submit_button("💾 Guardar Proyecto"):
            if nombre:
                nuevo_id = 1 if df_proy.empty else int(df_proy['ID_PROY'].max()) + 1
                sh.get_worksheet_by_id(0).append_row([nuevo_id, nombre, cliente])
                st.success(f"✅ Proyecto '{nombre}' guardado con ID {nuevo_id}")
                st.cache_data.clear()
            else:
                st.warning("El nombre es obligatorio.")

# --- MÓDULO 3: GESTIONAR ÍTEMS ---
elif opcion == "🏗️ Gestionar Ítems":
    st.subheader("Base de Datos de Ítems")
    df_items = load_data(50989702) # GID Ítems
    if df_items.empty:
        st.info("No hay ítems registrados.")
    else:
        st.dataframe(df_items, use_container_width=True, hide_index=True)
    
    # Aquí podrías agregar un formulario para crear nuevos ítems

# --- MÓDULO 4: GESTIONAR MATERIALES ---
elif opcion == "📦 Gestionar Materiales":
    st.subheader("Catálogo de Materiales")
    df_mat = load_data(1931749204) # GID Materiales
    if df_mat.empty:
        st.info("No hay materiales registrados.")
    else:
        st.dataframe(df_mat, use_container_width=True, hide_index=True)

# --- MÓDULO 5: CONSOLIDADO FINAL ---
elif opcion == "📊 Consolidado Final":
    st.header("Cálculo de Insumos")
    df_proy = load_data(0)
    if df_proy.empty:
        st.warning("Debe crear un proyecto primero.")
    else:
        proy_sel = st.selectbox("Proyecto a consultar", df_proy['NOMBRE'].unique())
        if st.button("Generar Reporte"):
            st.write(f"Procesando materiales para {proy_sel}...")
            # Aquí irá la lógica de merge que ya tenemos probada
