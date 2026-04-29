import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración y Conexión
st.set_page_config(page_title="Gestor Materiales 2026", layout="wide")

@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets.connections.gsheets)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    scopes = ["https://googleapis.com", "https://googleapis.com"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

client = get_client()
url_real = "https://google.com"
sh = client.open_by_url(url_real)

# 2. Función de carga genérica
@st.cache_data(ttl=60)
def load_data(gid):
    ws = sh.get_worksheet_by_id(gid)
    data = ws.get_all_records()
    return pd.DataFrame(data)

# --- NAVEGACIÓN (Botonera Lateral) ---
st.sidebar.title("Menú de Gestión")
opcion = st.sidebar.selectbox("Seleccione una opción", [
    "📁 Ver Proyectos", 
    "➕ Crear Proyecto", 
    "🏗️ Gestionar Ítems", 
    "📦 Gestionar Materiales",
    "📊 Consolidado Final"
])

st.title(f"Gestor 2026 > {opcion}")

# --- MÓDULO 1: VER PROYECTOS ---
if opcion == "📁 Ver Proyectos":
    df_proy = load_data(0) # GID 0
    if df_proy.empty:
        st.info("No hay proyectos registrados actualmente.")
    else:
        st.dataframe(df_proy, use_container_width=True, hide_index=True)

# --- MÓDULO 2: CREAR PROYECTO ---
elif opcion == "➕ Crear Proyecto":
    with st.form("form_nuevo_proy", clear_on_submit=True):
        st.subheader("Datos del nuevo proyecto")
        nombre = st.text_input("Nombre del Proyecto")
        cliente = st.text_input("Cliente")
        if st.form_submit_button("Guardar Proyecto"):
            # Lógica para ID y append_row aquí...
            st.success("Listo para programar el guardado de Proyecto")

# --- MÓDULO 3: GESTIONAR ÍTEMS ---
elif opcion == "🏗️ Gestionar Ítems":
    st.subheader("Configuración de Ítems de Obra")
    df_items = load_data(50989702)
    if df_items.empty:
        st.info("No hay ítems cargados.")
    else:
        st.dataframe(df_items, use_container_width=True)
    # Aquí irá el formulario para crear un Ítem (ID_ITEM, N_ITEM, etc.)

# --- MÓDULO 4: GESTIONAR MATERIALES ---
elif opcion == "📦 Gestionar Materiales":
    st.subheader("Base de Datos de Materiales")
    df_mat = load_data(1931749204)
    if df_mat.empty:
        st.info("La lista de materiales está vacía.")
    else:
        st.dataframe(df_mat, use_container_width=True)
    # Aquí irá el formulario para crear Material (ID_MAT, N_MAT, UNIDAD...)

# --- MÓDULO 5: CONSOLIDADO FINAL ---
elif opcion == "📊 Consolidado Final":
    st.subheader("Cálculo de Consumo por Proyecto")
    # Aquí irá tu lógica de merge y multiplicaciones que ya probamos
