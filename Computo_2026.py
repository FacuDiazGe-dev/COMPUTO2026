import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestor de Materiales 2026", layout="wide")

# 1. Configuración de Conexión (Usa los mismos secrets que ya tienes)
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Carga de datos usando los nombres de las pestañas (worksheets)
# TTL=600 mantiene los datos en caché por 10 minutos
sheet_url = "heet_url = "https://docs.google.com/spreadsheets/d/1ABC1234567890XYZ/edit#gid=0""

df_proyectos = conn.read(spreadsheet=sheet_url, worksheet="PROYECTOS", ttl=600)
df_materiales = conn.read(spreadsheet=sheet_url, worksheet="MATERIALES", ttl=600)
df_items = conn.read(spreadsheet=sheet_url, worksheet="ITEMS", ttl=600)
df_proy_detalle = conn.read(spreadsheet=sheet_url, worksheet="DETALLE_PROY", ttl=600)

st.title("Gestor de Materiales 2026")

# Menú lateral
modo = st.sidebar.radio("Navegación", ["Ver Consolidado", "Cargar Ítems"])

if modo == "Ver Consolidado":
    st.header("Consolidado de Proyecto")
    proyecto_sel = st.selectbox("Seleccionar Proyecto", df_proyectos['N_PROY'].unique())
    
    if st.button("Generar Listado"):
        # Obtener ID del proyecto seleccionado
        id_p = df_proyectos.loc[df_proyectos['N_PROY'] == proyecto_sel, 'ID_PROY'].values[0]
        
        # Filtrar detalle y realizar el merge para el cálculo
        det = df_proy_detalle[df_proy_detalle['ID_PROY'] == id_p].copy()
        
        if not det.empty:
            merged = det.merge(df_items, on='ID_ITEM')
            merged['CANT_TOTAL_MAT'] = merged['COMPUTO'] * merged['C_MAT']
            
            resumen = merged.groupby('ID_MAT')['CANT_TOTAL_MAT'].sum().reset_index()
            final = resumen.merge(df_materiales, on='ID_MAT')
            
            st.dataframe(final[['N_MAT', 'CANT_TOTAL_MAT', 'UNIDAD', 'COSTO_UNITARIO']], use_container_width=True)
        else:
            st.warning("Este proyecto no tiene ítems asignados aún.")

elif modo == "Cargar Ítems":
    st.header("Asignar Nuevo Ítem")
    
    with st.form("nuevo_item_form"):
        p_sel = st.selectbox("Proyecto", df_proyectos['N_PROY'].unique())
        i_sel = st.selectbox("Ítem de Obra", df_items['N_ITEM'].unique())
        cant = st.number_input("Cantidad (Cómputo)", min_value=0.0, step=0.1)
        
        btn_guardar = st.form_submit_button("Guardar en Sheet")
        
    if btn_guardar:
        # 1. Obtener los IDs (asegurando que sean escalares con [0])
        try:
            id_p = df_proyectos.loc[df_proyectos['N_PROY'] == p_sel, 'ID_PROY'].values[0]
            id_i = df_items.loc[df_items['N_ITEM'] == i_sel, 'ID_ITEM'].values[0]
            
            # 2. Crear el DataFrame de la nueva fila
            nueva_fila = pd.DataFrame([{
                "ID_PROY": id_p, 
                "ID_ITEM": id_i, 
                "COMPUTO": cant
            }])
            
            # 3. Concatenar con los datos previos
            # Es importante que las columnas coincidan exactamente con df_proy_detalle
            actualizado = pd.concat([df_proy_detalle, nueva_fila], ignore_index=True)
            
            # 4. Enviar a Google Sheets
            # El parámetro 'data' debe ser el DataFrame completo
            conn.update(
                spreadsheet=sheet_url, 
                worksheet="DETALLE_PROY", 
                data=actualizado
            )
            
            st.success(f"✅ Ítem '{i_sel}' añadido a '{p_sel}' con éxito.")
            
            # 5. Limpiar caché y REEJECUTAR para actualizar la vista inmediatamente
            st.cache_data.clear()
            st.rerun() 
    
        except IndexError:
            st.error("Error: No se encontró el ID del proyecto o del ítem.")
        except Exception as e:
            st.error(f"Hubo un problema al guardar: {e}")
#-----------------------------------------------import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de página
st.set_page_config(page_title="Gestor de Materiales 2026", layout="wide")

# 2. Inicializar Conexión
# Esto busca automáticamente el bloque [connections.gsheets] en tus Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. URL de tu planilla
sheet_url = "https://docs.google.com/spreadsheets/d/1ABC1234567890XYZ/edit#gid=0"

# 4. Carga de datos con caché integrado (TTL de 10 minutos)
df_proyectos = conn.read(spreadsheet=sheet_url, worksheet="PROYECTOS", ttl=600)
df_materiales = conn.read(spreadsheet=sheet_url, worksheet="MATERIALES", ttl=600)
df_items = conn.read(spreadsheet=sheet_url, worksheet="ITEMS", ttl=600)
df_proy_detalle = conn.read(spreadsheet=sheet_url, worksheet="DETALLE_PROY", ttl=600)

st.title("Gestor de Materiales 2026")

modo = st.sidebar.radio("Navegación", ["Ver Consolidado", "Cargar Ítems"])

if modo == "Ver Consolidado":
    st.header("Consolidado de Proyecto")
    proyecto_sel = st.selectbox("Seleccionar Proyecto", df_proyectos['N_PROY'].unique())
    
    if st.button("Generar Listado"):
        id_p = df_proyectos.loc[df_proyectos['N_PROY'] == proyecto_sel, 'ID_PROY'].values[0]
        
        # Filtrar detalle
        det = df_proy_detalle[df_proy_detalle['ID_PROY'] == id_p].copy()
        
        if not det.empty:
            # Merge con items para traer C_MAT y luego con materiales para nombres
            merged = det.merge(df_items, on='ID_ITEM')
            merged['CANT_TOTAL_MAT'] = merged['COMPUTO'] * merged['C_MAT']
            
            resumen = merged.groupby('ID_MAT')['CANT_TOTAL_MAT'].sum().reset_index()
            final = resumen.merge(df_materiales, on='ID_MAT')
            
            st.dataframe(final[['N_MAT', 'CANT_TOTAL_MAT', 'UNIDAD', 'COSTO_UNITARIO']])
        else:
            st.warning("No hay ítems cargados para este proyecto.")

elif modo == "Cargar Ítems":
    st.header("Asignar Ítems")
    with st.form("form_carga"):
        p_sel = st.selectbox("Proyecto", df_proyectos['N_PROY'].unique())
        i_sel = st.selectbox("Ítem", df_items['N_ITEM'].unique())
        cant = st.number_input("Cómputo", min_value=0.0, step=0.1)
        
        if st.form_submit_button("Guardar"):
            id_p = df_proyectos.loc[df_proyectos['N_PROY'] == p_sel, 'ID_PROY'].values[0]
            id_i = df_items.loc[df_items['N_ITEM'] == i_sel, 'ID_ITEM'].values[0]
            
            # Nueva fila
            nueva_fila = pd.DataFrame([{"ID_PROY": id_p, "ID_ITEM": id_i, "COMPUTO": cant}])
            
            # Unir y actualizar
            actualizado = pd.concat([df_proy_detalle, nueva_fila], ignore_index=True)
            conn.update(spreadsheet=sheet_url, worksheet="DETALLE_PROY", data=actualizado)
            
            st.success("¡Guardado!")
            st.cache_data.clear()
            st.rerun()
        
    
