import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# AÑADE ESTO PARA DIAGNÓSTICO
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    st.write(f"Intentando conectar con: {st.secrets.connections.gsheets['client_email']}")
else:
    st.error("No se detectó la configuración [connections.gsheets] en los Secrets.")
    
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
        
    
