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

# 1. SECCIÓN: CREAR PROYECTO
if modo == "➕ Crear Nuevo Proyecto":
    st.header("Registrar Nuevo Proyecto")
    with st.form("nuevo_proy_form", clear_on_submit=True):
        nombre_proy = st.text_input("Nombre del Proyecto")
        cliente = st.text_input("Cliente")
        if st.form_submit_button("Guardar Proyecto"):
            if nombre_proy:
                nuevo_id = 1 if df_proyectos.empty else int(df_proyectos['ID_PROY'].max()) + 1
                nueva_fila = [nuevo_id, nombre_proy, cliente]
                sh.worksheet("PROYECTOS").append_row(nueva_fila)
                st.success(f"Proyecto '{nombre_proy}' creado.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("El nombre es obligatorio.")

# 2. SECCIÓN: CARGAR ÍTEMS
elif modo == "🏗️ Cargar Ítems":
    st.header("Asignar Nuevo Ítem a Proyecto")
    if df_proyectos.empty:
        st.info("No hay proyectos. Crea uno primero.")
    else:
        with st.form("form_carga", clear_on_submit=True):
            p_sel = st.selectbox("Proyecto", df_proyectos['NOMBRE'].unique())
            i_sel = st.selectbox("Ítem de Obra", df_items['N_ITEM'].unique())
            cant = st.number_input("Cantidad (Cómputo)", min_value=0.0, step=0.1)
            
            if st.form_submit_button("Guardar Ítem"):
                try:
                    # CORRECCIÓN: 'NOMBRE' en lugar de 'NOMBREY'
                    id_p = df_proyectos.loc[df_proyectos['NOMBRE'] == p_sel, 'ID_PROY'].values[0]
                    id_i = df_items.loc[df_items['N_ITEM'] == i_sel, 'ID_ITEM'].values[0]
                    
                    nueva_fila = [int(id_p), int(id_i), float(cant)]
                    sh.worksheet("PROY_DETALLE").append_row(nueva_fila)
                    st.success("¡Guardado!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error: {e}")

# 3. SECCIÓN: VER CONSOLIDADO
elif modo == "📊 Ver Consolidado":
    st.header("Consolidado de Proyecto")
    if df_proyectos.empty or df_proy_detalle.empty:
        st.info("No hay datos suficientes para generar un consolidado.")
    else:
        proyecto_sel = st.selectbox("Seleccionar Proyecto", df_proyectos['NOMBRE'].unique())
        if st.button("Generar Listado"):
            id_p = df_proyectos.loc[df_proyectos['NOMBRE'] == proyecto_sel, 'ID_PROY'].values[0]
            det = df_proy_detalle[df_proy_detalle['ID_PROY'] == id_p].copy()
            
            if not det.empty:
                merged = det.merge(df_items, on='ID_ITEM')
                merged['CANT_TOTAL_MAT'] = merged['COMPUTO'] * merged['C_MAT']
                resumen = merged.groupby('ID_MAT')['CANT_TOTAL_MAT'].sum().reset_index()
                final = resumen.merge(df_materiales, on='ID_MAT')
                st.dataframe(final[['N_MAT', 'CANT_TOTAL_MAT', 'UNIDAD', 'COSTO_UNITARIO']], use_container_width=True)
            else:
                st.warning("Sin ítems en este proyecto.")

# SECCIÓN: CREAR PROYECTO---------------------------------------------------------------------
if modo == "➕ Crear Nuevo Proyecto":
    st.header("Registrar Nuevo Proyecto")
    
    with st.form("nuevo_proy_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nombre_proy = st.text_input("Nombre del Proyecto (ej: Edificio Centro)")
        with col2:
            cliente = st.text_input("Cliente / Empresa")
        
        submit = st.form_submit_button("🚀 Crear Proyecto")
        
        if submit:
            if nombre_proy:
                # Calculamos el nuevo ID basándonos en lo que ya existe
                # Si la tabla está vacía o solo tiene encabezados, el ID será 1
                try:
                    if not df_proyectos.empty and 'ID_PROY' in df_proyectos.columns:
                        nuevo_id = int(df_proyectos['ID_PROY'].max()) + 1
                    else:
                        nuevo_id = 1
                    
                    nueva_fila = [nuevo_id, nombre_proy, cliente]
                    
                    # Guardamos en la pestaña PROYECTOS (GID 0 usualmente)
                    sh.worksheet("PROYECTOS").append_row(nueva_fila)
                    
                    st.success(f"✅ Proyecto '{nombre_proy}' registrado con ID: {nuevo_id}")
                    
                    # Limpiamos caché y recargamos para que aparezca en "Cargar Ítems"
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar en Google Sheets: {e}")
            else:
                st.warning("Por favor, ingresa al menos el nombre del proyecto.")
