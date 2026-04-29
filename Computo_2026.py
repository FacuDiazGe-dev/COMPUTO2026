import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(page_title="Gestor Materiales 2026", layout="wide")
url_real = "https://docs.google.com/spreadsheets/d/12plATZeI3STturtJtMog24m-e-WNGr1KcAOWQRuvVO0/"

# ---------------------------------------------------------
# 2. CONEXIÓN (Mantenemos tu lógica probada)
# ---------------------------------------------------------
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

try:
    client = get_client()
    sh = client.open_by_url(url_real)
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. FUNCIÓN DE CARGA POR GID
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def load_data(gid):
    try:
        ws = sh.get_worksheet_by_id(gid)
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# ---------------------------------------------------------
# 4. NAVEGACIÓN (SIDEBAR)
# ---------------------------------------------------------
with st.sidebar:
    st.title("🏗️ Menú de Gestión")
    seccion = st.radio(
        "Seleccione una pestaña:",
        ["Inicio", "Edición de Bases", "Gestión de Proyectos"]
    )
    st.divider()
    # BOTÓN DE ACTUALIZACIÓN FORZADA
    if st.button("🔄 Actualizar Datos del Excel"):
        st.cache_data.clear()
        st.rerun()
    st.info("Sistema de Cómputo de Materiales v1.0")

# ---------------------------------------------------------
# 5. SECCIÓN: INICIO (RECEPCIÓN Y TABLA GENERAL)
# ---------------------------------------------------------
if seccion == "Inicio":
    st.header("📋 Panel de Proyectos Activos")
    
    # Cargamos datos de la Pestaña 4 (Proyectos_Items)
    df_proy_items = load_data(1900275728)
    
    if not df_proy_items.empty:
        # Mostramos proyectos únicos (agrupados)
        proyectos_unicos = df_proy_items[['ID_Proyecto', 'Nombre_Proyecto']].drop_duplicates()
        st.dataframe(proyectos_unicos, use_container_width=True, hide_index=True)
        
        # 5.a Selección para Informe Rápido
        st.subheader("📄 Emisión de Informe")
        p_sel = st.selectbox("Seleccione un proyecto para procesar:", proyectos_unicos['Nombre_Proyecto'])
        if st.button("Generar Resumen de Materiales"):
            st.warning("Lógica del condensador en desarrollo...")
    else:
        st.info("No hay proyectos registrados aún.")

# ---------------------------------------------------------
# 6. SECCIÓN: EDICIÓN DE BASES (MATERIALES Y RECETAS)
# ---------------------------------------------------------
elif seccion == "Edición de Bases":
    st.header("🧠 Repertorio Global")
    tab1, tab2 = st.tabs(["🛒 Catálogo de Materiales", "🍱 Recetas de Ítems"])
    
    # -----------------------------------------------------
    # 6.a APARTADO MATERIALES: Visualización y Carga
    # -----------------------------------------------------
    with tab1:
        st.subheader("Gestión de Insumos")
        
        # 1. CARGAR DATOS ACTUALES
        df_mat = load_data(0)
        
        # 2. FORMULARIO DE CARGA (DENTRO DEL EXPANDER)
        with st.expander("➕ Registrar Nuevo Material", expanded=False):
            with st.form("form_nuevo_material", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nuevo_id = st.text_input("ID Material (ej: MAT-001)")
                    nuevo_nombre = st.text_input("Nombre del Material")
                with col2:
                    nueva_unidad = st.text_input("Unidad (ej: kg, m3, unidad)")
                    nuevo_rubro = st.selectbox("Rubro Predeterminado", 
                        ["Albañilería", "Electricidad", "Plomería", "Estructura", "Terminaciones", "Aridos", "Otros"])
                
                btn_guardar_mat = st.form_submit_button("Guardar Material")

            # Lógica de guardado (DENTRO del expander, pero FUERA del form)
            if btn_guardar_mat:
                if nuevo_id and nuevo_nombre and nueva_unidad:
                    try:
                        ws_mat = sh.get_worksheet_by_id(0)
                        nueva_fila = [nuevo_id, nuevo_nombre, nueva_unidad, nuevo_rubro]
                        ws_mat.append_row(nueva_fila)
                        st.success(f"✅ Material '{nuevo_nombre}' guardado.")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("⚠️ Completa los campos obligatorios.")

        # 3. MODO EDICIÓN Y VISUALIZACIÓN
        if not df_mat.empty:
            st.write("💡 *Edita directamente en la tabla y presiona el botón inferior para guardar cambios.*")
            
            # Editor de datos (Reemplaza al dataframe simple)
            df_editado = st.data_editor(
                df_mat, 
                use_container_width=True, 
                hide_index=True,
                key="editor_materiales"
            )
            
            # Botón para confirmar cambios en la tabla
            if st.button("💾 Guardar Cambios en Tabla"):
                try:
                    ws_mat = sh.get_worksheet_by_id(0)
                    # Preparamos los datos: Encabezados + Filas
                    data_to_update = [df_editado.columns.values.tolist()] + df_editado.values.tolist()
                    ws_mat.update(data_to_update) # Esto pisa la hoja con lo nuevo
                    st.success("✅ Base de materiales actualizada.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar: {e}")
        else:
            st.info("El catálogo está vacío.")
        
    # ---------------------------------------------------------
    # 6.b APARTADO RECETAS: Definición de Ítems y su Composición
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Configuración de Ítems Tipo")
        
        # 1. CARGAR DATOS
        df_recetas = load_data(1931749204)      
        df_composicion = load_data(50989702)    
        df_materiales = load_data(0)            
    
        # 2. FORMULARIO: CREAR NUEVA RECETA
        with st.expander("➕ Crear Nueva Receta (Ítem)", expanded=False):
            with st.form("form_nueva_receta", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    r_id = st.text_input("ID Receta (ej: REC-001)")
                    r_nombre = st.text_input("Nombre del Ítem")
                with col2:
                    r_rubro = st.selectbox("Rubro", ["Albañilería", "Electricidad", "Plomería", "Estructura", "Aridos", "Otros"])
                
                btn_receta = st.form_submit_button("Crear Encabezado")
    
            if btn_receta:
                if r_id and r_nombre:
                    ws_rec = sh.get_worksheet_by_id(1931749204)
                    ws_rec.append_row([r_id, r_nombre, r_rubro])
                    st.success("✅ Ítem creado.")
                    st.cache_data.clear()
                    st.rerun()
    
        st.divider()

    # 1. BOTÓN DE REINICIO EN LA PARTE INFERIOR

    col_t, col_b = st.columns([4, 1])
    with col_b:
        if st.button("🧹 Limpiar Pantalla"):
            # Borramos las selecciones guardadas en la memoria de la sesión
            for key in st.session_state.keys():
                if "receta" in key or "mat" in key:
                    del st.session_state[key]
            st.rerun()
            
        # 3. ASIGNAR MATERIALES A RECETA
        st.subheader("🔗 Composición de la Receta")
            if not df_recetas.empty:
                # Usamos 'key' para que el botón de limpiar pueda resetearlo
                receta_sel = st.selectbox(
                    "Seleccione Ítem para editar su receta:", 
                    df_recetas['Nombre_Item'].unique(),
                    key="receta_activa"
                )
            # Extraemos el ID de forma segura como STRING
            id_receta_sel = str(df_recetas[df_recetas['Nombre_Item'] == receta_sel]['ID_Receta'].iloc[0])
    
            with st.form("form_agregar_material_receta", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    mat_nombres = df_materiales['Nombre'].tolist()
                    mat_elegido = st.selectbox("Seleccionar Material:", mat_nombres)
                    id_mat_elegido = str(df_materiales[df_materiales['Nombre'] == mat_elegido]['ID_Material'].iloc[0])
                
                # ESTE BLOQUE DEBE ESTAR ALINEADO CON "with c1"
                with c2:
                    cant_unitaria = st.number_input("Cantidad Unitaria (Incidencia)", min_value=0.000, format="%.3f", step=0.001)
                    factor_conv = st.number_input("Factor de Conversión (Divisor)", min_value=0.001, value=1.000, format="%.3f")
                
                # EL BOTÓN DEBE ESTAR DENTRO DEL "with st.form"
                btn_add_mat = st.form_submit_button("Añadir Material")

            # LA LÓGICA DE GUARDADO FUERA DEL FORMULARIO
            if btn_add_mat:
                try:
                    ws_comp = sh.get_worksheet_by_id(50989702)
                    ws_comp.append_row([id_receta_sel, id_mat_elegido, cant_unitaria, factor_conv])
                    st.success("✅ Material añadido correctamente.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            # 3. BOTÓN DE CIERRE DE EDICIÓN AL FINAL
            st.divider()
            if st.button("✅ Finalizar Edición de este Ítem"):
                st.success("Ítem guardado en base. Limpiando selección...")
                # Forzamos la limpieza del caché y el reinicio
                st.cache_data.clear()
                # Usamos un pequeño truco para resetear el selectbox
                st.session_state.receta_activa = df_recetas['Nombre_Item'].unique()[0] 
                st.rerun()

# 4. VISUALIZACIÓN DEL DETALLE (Con cálculo de Factor aplicado)
st.write(f"**Insumos en: {receta_sel}**")

if not df_composicion.empty and 'ID_Receta' in df_composicion.columns:
    # 1. Limpieza y preparación de datos
    df_composicion['ID_Receta'] = df_composicion['ID_Receta'].astype(str)
    id_receta_sel_str = str(id_receta_sel) # Aseguramos que sea string
    
    # 2. Filtrar materiales de la receta seleccionada
    detalle = df_composicion[df_composicion['ID_Receta'] == id_receta_sel_str].copy()
    
    if not detalle.empty:
        # 3. Asegurar que las columnas numéricas sean tratadas como tales
        detalle['Cantidad_Unitaria'] = pd.to_numeric(detalle['Cantidad_Unitaria'], errors='coerce')
        detalle['Factor'] = pd.to_numeric(detalle['Factor'], errors='coerce').fillna(1)
        
        # 4. APLICAR LA DIVISIÓN PARA MOSTRAR LA CANTIDAD FINAL
        detalle['Cantidad_Calculada'] = detalle['Cantidad_Unitaria'] / detalle['Factor']
        
        # 5. Unir con nombres de materiales
        df_materiales['ID_Material'] = df_materiales['ID_Material'].astype(str)
        resumen = detalle.merge(df_materiales[['ID_Material', 'Nombre', 'Unidad']], on='ID_Material', how='left')
        
        # 6. Mostrar la tabla con la columna ya calculada
        # Cambiamos el nombre de la columna para que el usuario entienda qué ve
        resumen = resumen.rename(columns={'Cantidad_Calculada': 'Cant. Real (incidencia)'})
        
        st.dataframe(
            resumen[['Nombre', 'Cant. Real (incidencia)', 'Unidad']], 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("No hay materiales en esta receta.")

# ---------------------------------------------------------
# 7. SECCIÓN: GESTIÓN DE PROYECTOS (CARGA Y EDICIÓN)
# ---------------------------------------------------------
elif seccion == "Gestión de Proyectos":
    st.header("🛠️ Operación de Proyectos")
    
    # 7.a Formulario para Crear / Cargar
    with st.expander("➕ Cargar Nuevo Ítem a Proyecto", expanded=True):
        # Aquí usaremos los selectbox alimentados por las bases globales
        st.write("Seleccione Proyecto, Ítem de la Base y asigne el Cómputo.")
        
    # 7.b Edición de Ítems cargados
    st.subheader("✏️ Ítems del Proyecto Seleccionado")



# ---------------------------------------------------------
# XX. CODIGO VIEJO QUE FUNCIONABA PARA USAR COMO EJEMPLO
# ---------------------------------------------------------
# import streamlit as st
# import pandas as pd
# import gspread
# from google.oauth2.service_account import Credentials

# # 1. CONFIGURACIÓN DE PÁGINA
# st.set_page_config(page_title="Gestor Materiales 2026", layout="wide")
# # Debes poner tu URL real, no "google.com"
# url_real = "https://docs.google.com/spreadsheets/d/12plATZeI3STturtJtMog24m-e-WNGr1KcAOWQRuvVO0/"

# # 2. CONEXIÓN
# @st.cache_resource
# def get_client():
#     creds_dict = dict(st.secrets.connections.gsheets)
#     creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

#     # Es obligatorio usar estas URLs completas
#     scopes = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive"
#     ]
    
#     creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
#     return gspread.authorize(creds)

# # Inicialización con manejo de errores visible
# try:
#     client = get_client()
#     sh = client.open_by_url(url_real)
# except Exception as e:
#     st.error(f"❌ Error de conexión: {e}")
#     st.info("Revisa que la URL sea correcta y que los SCOPES en el código sean las URLs completas.")
#     st.stop()

# # 3. FUNCIÓN DE CARGA POR GID
# @st.cache_data(ttl=60)
# def load_data(gid):
#     try:
#         ws = sh.get_worksheet_by_id(gid)
#         df = pd.DataFrame(ws.get_all_records())
#         df.columns = [str(c).strip() for c in df.columns] # Limpieza de nombres
#         return df
#     except:
#         return pd.DataFrame()

# # 4. NAVEGACIÓN (BOTONERA)
# st.sidebar.title("🛠️ Menú de Gestión")
# opcion = st.sidebar.selectbox("Seleccione una opción", [
#     "📁 Ver Proyectos", 
#     "➕ Crear Proyecto", 
#     "🏗️ Gestionar Ítems",
#     "📐 Cargar Cómputos",
#     "📦 Gestionar Materiales",
#     "📊 Consolidado Final"
# ])

# st.title(f"{opcion}")

# # --- MÓDULO 1: VER PROYECTOS ---
# if opcion == "📁 Ver Proyectos":
#     df_proy = load_data(0)
#     if df_proy.empty:
#         st.info("No hay proyectos registrados.")
#     else:
#         st.subheader("Listado de Proyectos")
#         st.dataframe(df_proy, use_container_width=True, hide_index=True)

# # --- MÓDULO 2: CREAR PROYECTO ---
# elif opcion == "➕ Crear Proyecto":
#     st.subheader("Registrar Nuevo Proyecto")
#     df_proy = load_data(0)
    
#     with st.form("form_nuevo_proy", clear_on_submit=True):
#         nombre = st.text_input("Nombre del Proyecto")
#         cliente = st.text_input("Cliente / Empresa")
        
#         if st.form_submit_button("💾 Guardar Proyecto"):
#             if nombre:
#                 # Generar ID
#                 nuevo_id = 1 if df_proy.empty else int(df_proy['ID_PROY'].max()) + 1
#                 nueva_fila = [nuevo_id, nombre, cliente]
                
#                 try:
#                     sh.get_worksheet_by_id(0).append_row(nueva_fila)
#                     st.success(f"✅ Proyecto '{nombre}' guardado con ID {nuevo_id}")
#                     st.cache_data.clear()
#                 except Exception as e:
#                     st.error(f"Error al escribir: {e}")
#             else:
#                 st.warning("El nombre es obligatorio.")


# # --- MÓDULO: CARGAR CÓMPUTOS ---
# elif opcion == "📐 Cargar Cómputos":
#     st.subheader("Asignación de Ítems a Proyectos")
    
#     df_proy = load_data(0)
#     df_items_base = load_data(50989702)
#     df_detalle = load_data(1900275728) # PROY_DETALLE
    
#     if df_proy.empty or df_items_base.empty:
#         st.warning("⚠️ Se requieren Proyectos e Ítems para continuar.")
#     else:
#         with st.form("form_computo", clear_on_submit=True):
#             col1, col2, col3 = st.columns([2, 2, 1])
            
#             with col1:
#                 proy_sel = st.selectbox("Proyecto", df_proy['NOMBRE'].unique())
            
#             with col2:
#                 # Obtenemos ítems únicos para el selector
#                 items_unicos = df_items_base[['ID_ITEM', 'N_ITEM', 'U_ITEM']].drop_duplicates('ID_ITEM')
#                 item_sel_nombre = st.selectbox("Ítem de Obra", items_unicos['N_ITEM'].unique())
            
#             with col3:
#                 unidad_txt = items_unicos.loc[items_unicos['N_ITEM'] == item_sel_nombre, 'U_ITEM'].values[0]
#                 cantidad_obra = st.number_input(f"Cantidad ({unidad_txt})", min_value=0.0, step=0.1)

#             if st.form_submit_button("➕ Registrar Cómputo"):
#                 if cantidad_obra > 0:
#                     try:
#                         # IDs de Proyecto e Ítem
#                         id_p = int(df_proy.loc[df_proy['NOMBRE'] == proy_sel, 'ID_PROY'].values[0])
#                         id_i = int(items_unicos.loc[items_unicos['N_ITEM'] == item_sel_nombre, 'ID_ITEM'].values[0])
                        
#                         # Lógica robusta para ID_CARGA (Autoincremental)
#                         if df_detalle.empty or 'ID_CARGA' not in df_detalle.columns or df_detalle['ID_CARGA'].isnull().all():
#                             nuevo_id_carga = 1
#                         else:
#                             nuevo_id_carga = int(pd.to_numeric(df_detalle['ID_CARGA'], errors='coerce').max()) + 1
                        
#                         # Estructura: [ID_CARGA, ID_PROY, ID_ITEM, COMPUTO]
#                         nueva_fila = [nuevo_id_carga, id_p, id_i, cantidad_obra]
                        
#                         sh.get_worksheet_by_id(1900275728).append_row(nueva_fila)
                        
#                         st.success(f"✅ Registrado: {item_sel_nombre} en {proy_sel} (Carga #{nuevo_id_carga})")
#                         st.cache_data.clear()
#                         st.rerun()
#                     except Exception as e:
#                         st.error(f"Error técnico al vincular: {e}")
#                 else:
#                     st.error("La cantidad debe ser mayor a 0.")

#         # Visualización de lo cargado en el proyecto seleccionado
#         st.divider()
#         st.write(f"### Detalle de obra: {proy_sel}")
        
#         if not df_detalle.empty:
#             id_p_actual = df_proy.loc[df_proy['NOMBRE'] == proy_sel, 'ID_PROY'].values[0]
#             # Filtrado estricto por ID_PROY
#             mis_items = df_detalle[pd.to_numeric(df_detalle['ID_PROY']) == int(id_p_actual)]
            
#             if not mis_items.empty:
#                 # Merge con la base de ítems para mostrar nombres
#                 tabla_visual = mis_items.merge(items_unicos, on='ID_ITEM', how='left')
#                 st.dataframe(
#                     tabla_visual[['ID_CARGA', 'N_ITEM', 'COMPUTO', 'U_ITEM']], 
#                     use_container_width=True, 
#                     hide_index=True
#                 )
#             else:
#                 st.info("No hay cómputos cargados para este proyecto.")


# # --- MÓDULO 3: GESTIONAR ÍTEMS ---
# elif opcion == "🏗️ Gestionar Ítems":
#     st.subheader("Análisis de Materiales por Ítem")
    
#     df_mat = load_data(1931749204)
#     df_items = load_data(50989702)

#     if not df_items.empty:
#         df_items['ID_ITEM'] = pd.to_numeric(df_items['ID_ITEM'], errors='coerce')

#     if "receta_temporal" not in st.session_state:
#         st.session_state.receta_temporal = []

#     # 1. Definición del Ítem (Nombre y su Unidad de medida global)
#     col_n1, col_n2 = st.columns([3, 1])
#     with col_n1:
#         n_item_nuevo = st.text_input("Nombre del Ítem", placeholder="Ej: Contrapiso de Cascotes").strip()
#     with col_n2:
#         u_item = st.selectbox("Unidad del Ítem", ["m2", "m3", "ml", "un", "kg", "gl"])
    
#     if n_item_nuevo and not df_items.empty:
#         if n_item_nuevo.lower() in df_items['N_ITEM'].str.lower().unique():
#             st.warning(f"⚠️ El ítem '{n_item_nuevo}' ya existe.")

#     # 2. Selector de Insumos
#     with st.container(border=True):
#         c1, c2, c3 = st.columns([2, 1, 1])
#         with c1:
#             col_n = 'NOMBRE' if 'NOMBRE' in df_mat.columns else 'N_MAT'
#             mat_sel = st.selectbox("Insumo a añadir", df_mat[col_n].unique() if not df_mat.empty else ["No hay materiales"])
#         with c2:
#             cantidad_insumo = st.number_input("Cantidad/Consumo (C_MAT)", min_value=0.0, format="%.4f")
#         with c3:
#             st.write(" ")
#             if st.button("➕ Añadir Insumo", use_container_width=True):
#                 if not df_mat.empty and cantidad_insumo > 0:
#                     # Extraemos la fila del material
#                     material_row = df_mat[df_mat[col_n] == mat_sel].iloc[0]
#                     st.session_state.receta_temporal.append({
#                         "ID_MAT": material_row['ID_MAT'],
#                         "Material": mat_sel,
#                         "C_MAT": cantidad_insumo,
#                         "Unidad_Mat": material_row['UNIDAD']
#                     })

#     # 3. Tabla Temporal y Guardado
#     if st.session_state.receta_temporal:
#         st.write("### Vista Previa de la Receta")
#         df_temp = pd.DataFrame(st.session_state.receta_temporal)
#         st.table(df_temp[['Material', 'C_MAT', 'Unidad_Mat']])

#         col_acc1, col_acc2 = st.columns(2)
#         with col_acc1:
#             if st.button("🗑️ Vaciar Lista", use_container_width=True):
#                 st.session_state.receta_temporal = []
#                 st.rerun()
        
#         with col_acc2:
#             if st.button("💾 CONFIRMAR Y SUBIR A GSHEETS", type="primary", use_container_width=True):
#                 if not n_item_nuevo:
#                     st.error("Falta el nombre del Ítem.")
#                 else:
#                     # Lógica de ID autoincremental
#                     if df_items.empty or df_items['ID_ITEM'].isnull().all():
#                         nuevo_id_i = 1
#                     else:
#                         nuevo_id_i = int(df_items['ID_ITEM'].max()) + 1
                    
#                     # --- ORDEN DE COLUMNAS CRÍTICO ---
#                     # Estructura: [ID_ITEM, N_ITEM, U_ITEM, ID_MAT, C_MAT]
#                     filas_batch = []
#                     for r in st.session_state.receta_temporal:
#                         filas_batch.append([
#                             int(nuevo_id_i),      # ID del ítem
#                             str(n_item_nuevo),   # Nombre
#                             str(u_item),         # Unidad del cómputo (m2, m3, etc)
#                             int(r['ID_MAT']),    # ID del material (pestaña maestra)
#                             float(r['C_MAT'])    # Coeficiente de consumo
#                         ])
                    
#                     try:
#                         sh.get_worksheet_by_id(50989702).append_rows(filas_batch)
#                         st.success(f"✅ Ítem '{n_item_nuevo}' guardado con éxito.")
#                         st.session_state.receta_temporal = []
#                         st.cache_data.clear()
#                         st.rerun()
#                     except Exception as e:
#                         st.error(f"Error de comunicación: {e}")
                        

# # --- MÓDULO 4: GESTIONAR MATERIALES ---
# elif opcion == "📦 Gestionar Materiales":
#     st.subheader("Catálogo Maestro de Materiales")
    
#     df_mat = load_data(1931749204)
    
#     LISTA_RUBROS = ["Cementos", "Áridos", "Metales", "Albañilería", "Chapas", "Aislaciones", "Instalaciones", "Otros"]
    
#     with st.expander("➕ Agregar Nuevo Material al Catálogo", expanded=df_mat.empty):
#         with st.form("form_nuevo_material", clear_on_submit=True):
#             col1, col2 = st.columns(2)
#             with col1:
#                 n_mat = st.text_input("Nombre del Material")
#                 rubro_sel = st.selectbox("Rubro", LISTA_RUBROS)
#             with col2:
#                 unidad = st.selectbox("Unidad", ["m3", "kg", "un", "lts", "m2", "gl", "barra"])
#                 costo = st.number_input("Costo Unitario ($)", min_value=0.0, step=0.1)
            
#             if st.form_submit_button("Guardar Material"):
#                 if n_mat:
#                     # Lógica de ID: Seguiremos guardando el NÚMERO puro en Google Sheets
#                     # pero lo calculamos para que sea único.
#                     nuevo_id_num = 1 if df_mat.empty else int(df_mat['ID_MAT'].max()) + 1
                    
#                     # Guardamos la fila (Asegúrate que el orden coincida con tu GSheet)
#                     # Sugerencia de orden: [ID_MAT, NOMBRE, UNIDAD, COSTO, RUBRO]
#                     nueva_fila_mat = [nuevo_id_num, n_mat, unidad, costo, rubro_sel]
                    
#                     try:
#                         sh.get_worksheet_by_id(1931749204).append_row(nueva_fila_mat)
#                         st.success(f"✅ Material '{n_mat}' guardado con ID #{nuevo_id_num}")
#                         st.cache_data.clear()
#                         st.rerun()
#                     except Exception as e:
#                         st.error(f"Error al guardar: {e}")
#                 else:
#                     st.warning("El nombre del material es obligatorio.")

#     # Visualización con "Código Visual"
#     if not df_mat.empty:
#         st.write("### Inventario")
        
#         # Creamos una columna visual que combine Rubro + ID solo para mostrarla
#         # Esto no se guarda en el Excel, solo se ve en la web
#         df_visual = df_mat.copy()
#         df_visual['COD_VISUAL'] = df_visual.apply(
#             lambda x: f"{str(x['RUBRO'])[:3].upper()}-{str(x['ID_MAT']).zfill(3)}", axis=1
#         )
        
#         # Reordenamos columnas para que el código visual esté primero
#         cols = ['COD_VISUAL', 'NOMBRE', 'RUBRO', 'UNIDAD', 'COSTO']
#         # Filtramos solo las que existen para evitar errores
#         cols_presentes = [c for c in cols if c in df_visual.columns]
        
#         st.dataframe(df_visual[cols_presentes], use_container_width=True, hide_index=True)

# # --- MÓDULO 5: CONSOLIDADO FINAL ---
# # --- MÓDULO 5: CONSOLIDADO FINAL ---
# elif opcion == "📊 Consolidado Final":
#     st.header("📊 Resumen de Materiales por Proyecto")
    
#     # 1. Carga de todas las bases necesarias
#     df_proy = load_data(0)
#     df_mat_maestro = load_data(1931749204)  # M_MATERIALES
#     df_items_recetas = load_data(50989702)  # ITEMS (Recetas)
#     df_computos = load_data(1900275728)      # PROY_DETALLE (Cómputos)

#     if df_computos.empty or df_items_recetas.empty:
#         st.warning("⚠️ No hay cómputos cargados o recetas definidas para generar un reporte.")
#     else:
#         proy_sel = st.selectbox("Seleccionar Proyecto", df_proy['NOMBRE'].unique())
        
#         if st.button("🚀 Calcular Listado de Materiales"):
#             # A. Obtener ID del proyecto
#             id_p = int(df_proy.loc[df_proy['NOMBRE'] == proy_sel, 'ID_PROY'].values[0])
            
#             # B. Filtrar cómputos del proyecto
#             mis_computos = df_computos[df_computos['ID_PROY'] == id_p].copy()
            
#             if mis_computos.empty:
#                 st.error("Este proyecto no tiene ítems asignados.")
#             else:
#                 # C. Vincular Cómputos con Recetas (Trae ID_MAT y C_MAT)
#                 # Usamos merge por ID_ITEM
#                 df_unificado = mis_computos.merge(df_items_recetas, on='ID_ITEM', how='inner')
                
#                 # D. Cálculo de cantidades totales
#                 # Cantidad Total = Cantidad de Obra (COMPUTO) * Coeficiente Material (C_MAT)
#                 df_unificado['TOTAL_INSUMO'] = df_unificado['COMPUTO'] * df_unificado['C_MAT']
                
#                 # E. Agrupar por Material (por si varios ítems usan el mismo material)
#                 resumen_insumos = df_unificado.groupby('ID_MAT')['TOTAL_INSUMO'].sum().reset_index()
                
#                 # F. Traer nombres y unidades desde el maestro de materiales
#                 final = resumen_insumos.merge(df_mat_maestro, on='ID_MAT', how='left')
                
#                 # --- CORRECCIÓN DE NOMBRES DE COLUMNAS ---
#                 # Detectamos qué columnas existen realmente para evitar el KeyError
#                 col_nombre_mat = 'NOMBRE' if 'NOMBRE' in final.columns else 'N_MAT'
                
#                 st.subheader(f"Listado para: {proy_sel}")
                
#                 # Definimos qué mostrar según lo que exista en tu GSheet
#                 columnas_ver = [col_nombre_mat, 'TOTAL_INSUMO', 'UNIDAD']
#                 # Si agregaste RUBRO, lo incluimos
#                 if 'RUBRO' in final.columns: columnas_ver.append('RUBRO')
                
#                 # Filtramos solo las que existen para el dataframe
#                 cols_finales = [c for c in columnas_ver if c in final.columns]
                
#                 st.dataframe(
#                     final[cols_finales].sort_values(by=cols_finales[-1] if 'RUBRO' in cols_finales else col_nombre_mat),
#                     use_container_width=True,
#                     hide_index=True
#                 )

#                 # Opción de descarga
#                 csv = final[cols_finales].to_csv(index=False).encode('utf-8')
#                 st.download_button("📥 Descargar CSV", csv, f"Consolidado_{proy_sel}.csv", "text/csv")
