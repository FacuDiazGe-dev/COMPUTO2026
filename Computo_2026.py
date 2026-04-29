import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Gestor de Materiales 2026", layout="wide")

# 1. Configuración de Conexión (Usa los mismos secrets que ya tienes)
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Carga de datos usando los nombres de las pestañas (worksheets)
# TTL=600 mantiene los datos en caché por 10 minutos
sheet_url = "https://google.com"

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
            id_p = df_proyectos.loc[df_proyectos['N_PROY'] == p_sel, 'ID_PROY'].values[0]
            id_i = df_items.loc[df_items['N_ITEM'] == i_sel, 'ID_ITEM'].values[0]
            
            # Crear DataFrame con la nueva fila
            nueva_fila = pd.DataFrame([{"ID_PROY": id_p, "ID_ITEM": id_i, "COMPUTO": cant}])
            
            # Actualizar el Google Sheet (esto añade la fila al final)
            # Nota: El conector lee la hoja actual, concatena y vuelve a escribir
            actualizado = pd.concat([df_proy_detalle, nueva_fila], ignore_index=True)
            conn.update(spreadsheet=sheet_url, worksheet="DETALLE_PROY", data=actualizado)
            
            st.success("¡Ítem guardado correctamente!")
            st.cache_data.clear() # Limpiar caché para ver los cambios
        
    
