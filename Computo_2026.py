import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestor Materiales 2026", layout="wide")

# URL REAL CENTRALIZADA
url_real = "https://google.com"

# 2. CONEXIÓN (SCOPES CORRECTOS)
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

# Inicialización
try:
    client = get_client()
    sh = client.open_by_url(url_real)
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# 3. FUNCIÓN DE CARGA POR GID
@st.cache_data(ttl=60)
def load_data(gid):
    try:
        ws = sh.get_worksheet_by_id(gid)
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [str(c).strip() for c in df.columns] # Limpieza de nombres
        return df
    except:
        return pd.DataFrame()

# 4. NAVEGACIÓN (BOTONERA)
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
    df_proy = load_data(0)
    if df_proy.empty:
        st.info("No hay proyectos registrados.")
    else:
        st.subheader("Listado de Proyectos")
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
                # Generar ID
                nuevo_id = 1 if df_proy.empty else int(df_proy['ID_PROY'].max()) + 1
                nueva_fila = [nuevo_id, nombre, cliente]
                
                try:
                    sh.get_worksheet_by_id(0).append_row(nueva_fila)
                    st.success(f"✅ Proyecto '{nombre}' guardado con ID {nuevo_id}")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error al escribir: {e}")
            else:
                st.warning("El nombre es obligatorio.")

# --- MÓDULO 3: GESTIONAR ÍTEMS ---
elif opcion == "🏗️ Gestionar Ítems":
    st.subheader("Base de Datos de Ítems")
    df_items = load_data(50989702)
    if df_items.empty:
        st.info("No hay ítems registrados.")
    else:
        st.dataframe(df_items, use_container_width=True, hide_index=True)

# --- MÓDULO 4: GESTIONAR MATERIALES ---
elif opcion == "📦 Gestionar Materiales":
    st.subheader("Catálogo de Materiales")
    df_mat = load_data(1931749204)
    if df_mat.empty:
        st.info("No hay materiales registrados.")
    else:
        st.dataframe(df_mat, use_container_width=True, hide_index=True)

# --- MÓDULO 5: CONSOLIDADO FINAL ---
elif opcion == "📊 Consolidado Final":
    st.header("Cálculo de Insumos")
    df_proy = load_data(0)
    df_items = load_data(50989702)
    df_materiales = load_data(1931749204)
    df_proy_detalle = load_data(1900275728)

    if df_proy.empty or df_proy_detalle.empty:
        st.warning("No hay datos suficientes (proyectos o ítems cargados).")
    else:
        proy_sel = st.selectbox("Seleccionar Proyecto", df_proy['NOMBRE'].unique())
        if st.button("🔍 Generar Reporte"):
            # Lógica de cálculo
            id_p = df_proy.loc[df_proy['NOMBRE'] == proy_sel, 'ID_PROY'].values[0]
            det = df_proy_detalle[df_proy_detalle['ID_PROY'] == id_p].copy()
            
            if not det.empty:
                merged = det.merge(df_items, on='ID_ITEM')
                merged['CANT_TOTAL_MAT'] = merged['COMPUTO'] * merged['C_MAT']
                resumen = merged.groupby('ID_MAT')['CANT_TOTAL_MAT'].sum().reset_index()
                final = resumen.merge(df_materiales, on='ID_MAT')
                
                st.dataframe(final[['N_MAT', 'CANT_TOTAL_MAT', 'UNIDAD', 'COSTO_UNITARIO']], use_container_width=True)
            else:
                st.info("Este proyecto aún no tiene ítems asignados.")
