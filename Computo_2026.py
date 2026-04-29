import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de página
st.set_page_config(page_title="Gestor de Materiales 2026", layout="wide")

# 2. Conexión Silenciosa (Sin mensajes de diagnóstico)
@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets.connections.gsheets)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# 3. Inicialización
client = get_client()
url_real = "https://docs.google.com/spreadsheets/d/12plATZeI3STturtJtMog24m-e-WNGr1KcAOWQRuvVO0/"
sh = client.open_by_url(url_real)

# 4. Funciones de carga con caché
@st.cache_data(ttl=600)
def load_data(worksheet_name):
    ws = sh.worksheet(worksheet_name)
    return pd.DataFrame(ws.get_all_records())

# Carga inicial de DataFrames
df_proyectos = load_data("PROYECTOS")
df_materiales = load_data("M_MATERIALES")
df_items = load_data("ITEMS")
df_proy_detalle = load_data("PROY_DETALLE")

# --- INTERFAZ ---
st.title("🏗️ Gestor de Materiales 2026")
modo = st.sidebar.radio("Navegación", ["Ver Consolidado", "Cargar Ítems"])

if modo == "Ver Consolidado":
    st.header("Consolidado de Proyecto")
    
    # Usamos 'NOMBRE' en lugar de 'N_PROY'
    proyecto_sel = st.selectbox("Seleccionar Proyecto", df_proyectos['NOMBRE'].unique())
    
    if st.button("Generar Listado"):
        # También actualizamos aquí para buscar el ID usando la columna 'NOMBRE'
        id_p = df_proyectos.loc[df_proyectos['NOMBRE'] == proyecto_sel, 'ID_PROY'].values[0]
        
        # Filtrar detalle y calcular
        det = df_proy_detalle[df_proy_detalle['ID_PROY'] == id_p].copy()
        
        if not det.empty:
            merged = det.merge(df_items, on='ID_ITEM')
            merged['CANT_TOTAL_MAT'] = merged['COMPUTO'] * merged['C_MAT']
            
            resumen = merged.groupby('ID_MAT')['CANT_TOTAL_MAT'].sum().reset_index()
            final = resumen.merge(df_materiales, on='ID_MAT')
            
            st.dataframe(
                final[['N_MAT', 'CANT_TOTAL_MAT', 'UNIDAD', 'COSTO_UNITARIO']], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Este proyecto no tiene ítems asignados.")

elif modo == "Cargar Ítems":
    st.header("Asignar Nuevo Ítem a Proyecto")
    
    with st.form("form_carga", clear_on_submit=True):
        p_sel = st.selectbox("Proyecto", df_proyectos['NOMBRE'].unique())
        i_sel = st.selectbox("Ítem de Obra", df_items['N_ITEM'].unique())
        cant = st.number_input("Cantidad (Cómputo)", min_value=0.0, step=0.1)
        
        btn_guardar = st.form_submit_button("Guardar Ítem")
        
        if btn_guardar:
            try:
                # Obtener IDs
                id_p = df_proyectos.loc[df_proyectos['NOMBREY'] == p_sel, 'ID_PROY'].values[0]
                id_i = df_items.loc[df_items['N_ITEM'] == i_sel, 'ID_ITEM'].values[0]
                
                # Preparar fila (Ajusta el orden según tus columnas en Google Sheets)
                # Ejemplo: [ID_PROY, ID_ITEM, COMPUTO]
                nueva_fila = [int(id_p), int(id_i), float(cant)]
                
                # Escribir en Google Sheets
                sh.worksheet("DETALLE_PROY").append_row(nueva_fila)
                
                st.success(f"✅ ¡{i_sel} guardado en {p_sel}!")
                st.cache_data.clear() # Limpiar caché para que aparezca en el consolidado
            except Exception as e:
                st.error(f"Error al guardar: {e}")
#--------------------------------------------------------------------------------------

# --- LÓGICA PARA TABLA VACÍA ---
# Si el DF está vacío, creamos uno con las columnas necesarias para que el código no falle
if df_proyectos.empty:
    df_proyectos = pd.DataFrame(columns=['ID_PROY', 'NOMBRE', 'CLIENTE'])

# --- MENÚ DE NAVEGACIÓN ---
modo = st.sidebar.selectbox("Seleccionar Acción", 
    ["📊 Ver Consolidado", "🏗️ Cargar Ítems", "➕ Crear Nuevo Proyecto"])

# --- SECCIÓN: CREAR PROYECTO ---
if modo == "➕ Crear Nuevo Proyecto":
    st.header("Registrar Nuevo Proyecto")
    with st.form("nuevo_proy_form", clear_on_submit=True):
        nombre_proy = st.text_input("Nombre del Proyecto (ej: Edificio Alvear)")
        cliente = st.text_input("Cliente")
        
        if st.form_submit_button("Guardar Proyecto"):
            if nombre_proy:
                # Generar un ID nuevo (el último + 1, o 1 si está vacío)
                nuevo_id = 1 if df_proyectos.empty else int(df_proyectos['ID_PROY'].max()) + 1
                
                nueva_fila = [nuevo_id, nombre_proy, cliente]
                
                try:
                    sh.get_worksheet_by_id(0).append_row(nueva_fila)
                    st.success(f"Proyecto '{nombre_proy}' creado con éxito (ID: {nuevo_id})")
                    st.cache_data.clear() # Forzamos recarga para que aparezca en los selectores
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("El nombre del proyecto es obligatorio.")

# --- SECCIÓN: VER CONSOLIDADO (CON PREVISIÓN DE VACÍO) ---
elif modo == "📊 Ver Consolidado":
    st.header("Consolidado de Proyecto")
    
    if df_proyectos.empty:
        st.info("No hay proyectos registrados. Ve a 'Crear Nuevo Proyecto'.")
    else:
        proyecto_sel = st.selectbox("Seleccionar Proyecto", df_proyectos['NOMBRE'].unique())
        # ... resto de tu código de cálculo ...

# --- SECCIÓN: CARGAR ÍTEMS (CON PREVISIÓN DE VACÍO) ---
elif modo == "🏗️ Cargar Ítems":
    st.header("Asignar Ítems")
    if df_proyectos.empty:
        st.info("Primero debes crear un proyecto.")
    else:
        # ... tu formulario de carga de ítems ...
        pass
