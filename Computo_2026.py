import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gestor Materiales 2026", layout="wide")

# --- ERROR 1 CORREGIDO: URL DEL SPREADSHEET ---
# Debes poner tu URL real, no "google.com"
url_real = "https://docs.google.com/spreadsheets/d/12plATZeI3STturtJtMog24m-e-WNGr1KcAOWQRuvVO0/"

# 2. CONEXIÓN
@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets.connections.gsheets)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    # --- ERROR 2 CORREGIDO: SCOPES COMPLETOS ---
    # Es obligatorio usar estas URLs completas
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# Inicialización con manejo de errores visible
try:
    client = get_client()
    sh = client.open_by_url(url_real)
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.info("Revisa que la URL sea correcta y que los SCOPES en el código sean las URLs completas.")
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
# --- MÓDULO 3: GESTIONAR ÍTEMS (Análisis de Composición) ---
elif opcion == "🏗️ Gestionar Ítems":
    st.subheader("Análisis de Materiales por Ítem")
    
    df_mat = load_data(1931749204)
    df_items = load_data(50989702)

    # Limpieza de IDs para evitar errores de tipo
    if not df_items.empty:
        df_items['ID_ITEM'] = pd.to_numeric(df_items['ID_ITEM'], errors='coerce')

    if "receta_temporal" not in st.session_state:
        st.session_state.receta_temporal = []

    # 1. Definición del Nombre del Ítem
    n_item_nuevo = st.text_input("Nombre del Ítem", placeholder="Ej: Contrapiso de Cascotes").strip()
    
    # Validación de existencia previa
    if n_item_nuevo and not df_items.empty:
        if n_item_nuevo.lower() in df_items['N_ITEM'].str.lower().unique():
            st.warning(f"⚠️ El ítem '{n_item_nuevo}' ya existe en la base de datos.")

    # 2. Selector de Insumos (Sin Precios)
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            col_n = 'NOMBRE' if 'NOMBRE' in df_mat.columns else 'N_MAT'
            mat_sel = st.selectbox("Insumo a añadir", df_mat[col_n].unique() if not df_mat.empty else ["No hay materiales"])
        with c2:
            cantidad = st.number_input("Cantidad/Consumo", min_value=0.0, format="%.4f")
        with c3:
            st.write(" ")
            if st.button("➕ Añadir Insumo", use_container_width=True):
                if not df_mat.empty and cantidad > 0:
                    material_row = df_mat[df_mat[col_n] == mat_sel].iloc[0]
                    st.session_state.receta_temporal.append({
                        "ID_MAT": material_row['ID_MAT'],
                        "Material": mat_sel,
                        "Cantidad": cantidad,
                        "Unidad": material_row['UNIDAD']
                    })
                else:
                    st.error("Verifica que exista el material y la cantidad sea mayor a 0.")

    # 3. Tabla Temporal y Guardado
    if st.session_state.receta_temporal:
        st.write("### Composición Temporal del Ítem")
        df_temp = pd.DataFrame(st.session_state.receta_temporal)
        st.table(df_temp[['Material', 'Cantidad', 'Unidad']])

        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            if st.button("🗑️ Vaciar Lista", use_container_width=True):
                st.session_state.receta_temporal = []
                st.rerun()
        
        with col_acc2:
            if st.button("💾 CONFIRMAR Y SUBIR A GSHEETS", type="primary", use_container_width=True):
                if not n_item_nuevo:
                    st.error("Falta el nombre del Ítem.")
                else:
                    # Lógica de ID autoincremental
                    nuevo_id_i = 1 if (df_items.empty or df_items['ID_ITEM'].isnull().all()) else int(df_items['ID_ITEM'].max()) + 1
                    
                    filas_batch = [[nuevo_id_i, n_item_nuevo, r['ID_MAT'], r['Cantidad']] 
                                   for r in st.session_state.receta_temporal]
                    
                    try:
                        sh.get_worksheet_by_id(50989702).append_rows(filas_batch)
                        st.success(f"Ítem '{n_item_nuevo}' (ID: {nuevo_id_i}) guardado con éxito.")
                        st.session_state.receta_temporal = []
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error de comunicación: {e}")

# --- MÓDULO 4: GESTIONAR MATERIALES ---
elif opcion == "📦 Gestionar Materiales":
    st.subheader("Catálogo Maestro de Materiales")
    
    df_mat = load_data(1931749204)
    
    LISTA_RUBROS = ["Cementos", "Áridos", "Metales", "Albañilería", "Chapas", "Aislaciones", "Instalaciones", "Otros"]
    
    with st.expander("➕ Agregar Nuevo Material al Catálogo", expanded=df_mat.empty):
        with st.form("form_nuevo_material", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                n_mat = st.text_input("Nombre del Material")
                rubro_sel = st.selectbox("Rubro", LISTA_RUBROS)
            with col2:
                unidad = st.selectbox("Unidad", ["m3", "kg", "un", "lts", "m2", "gl", "barra"])
                costo = st.number_input("Costo Unitario ($)", min_value=0.0, step=0.1)
            
            if st.form_submit_button("Guardar Material"):
                if n_mat:
                    # Lógica de ID: Seguiremos guardando el NÚMERO puro en Google Sheets
                    # pero lo calculamos para que sea único.
                    nuevo_id_num = 1 if df_mat.empty else int(df_mat['ID_MAT'].max()) + 1
                    
                    # Guardamos la fila (Asegúrate que el orden coincida con tu GSheet)
                    # Sugerencia de orden: [ID_MAT, NOMBRE, UNIDAD, COSTO, RUBRO]
                    nueva_fila_mat = [nuevo_id_num, n_mat, unidad, costo, rubro_sel]
                    
                    try:
                        sh.get_worksheet_by_id(1931749204).append_row(nueva_fila_mat)
                        st.success(f"✅ Material '{n_mat}' guardado con ID #{nuevo_id_num}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.warning("El nombre del material es obligatorio.")

    # Visualización con "Código Visual"
    if not df_mat.empty:
        st.write("### Inventario")
        
        # Creamos una columna visual que combine Rubro + ID solo para mostrarla
        # Esto no se guarda en el Excel, solo se ve en la web
        df_visual = df_mat.copy()
        df_visual['COD_VISUAL'] = df_visual.apply(
            lambda x: f"{str(x['RUBRO'])[:3].upper()}-{str(x['ID_MAT']).zfill(3)}", axis=1
        )
        
        # Reordenamos columnas para que el código visual esté primero
        cols = ['COD_VISUAL', 'NOMBRE', 'RUBRO', 'UNIDAD', 'COSTO']
        # Filtramos solo las que existen para evitar errores
        cols_presentes = [c for c in cols if c in df_visual.columns]
        
        st.dataframe(df_visual[cols_presentes], use_container_width=True, hide_index=True)

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
