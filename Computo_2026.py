import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.title("🧪 Diagnóstico de Conexión Extremo")

# 1. Verificar si existen los Secrets
st.subheader("1. Verificando Secrets")
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    info = st.secrets.connections.gsheets
    st.write(f"✅ Sección [connections.gsheets] encontrada.")
    st.write(f"📧 Email de cuenta de servicio: `{info.get('client_email')}`")
    st.write(f"🆔 Project ID: `{info.get('project_id')}`")
else:
    st.error("❌ No se encuentran los secrets bajo [connections.gsheets]")
    st.stop()

# 2. Intentar crear las credenciales
st.subheader("2. Creando credenciales")
try:
    creds_dict = dict(st.secrets.connections.gsheets)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    st.write("✅ Objeto de credenciales creado correctamente.")
except Exception as e:
    st.error(f"❌ Fallo al crear credenciales: {e}")
    st.stop()

# 3. Intentar acceder al Spreadsheet
st.subheader("3. Accediendo al archivo")
# CAMBIA ESTO POR TU URL REAL
url_real = "https://docs.google.com/spreadsheets/d//12plATZeI3STturtJtMog24m-e-WNGr1KcAOWQRuvVO0/edit?gid=0#gid=0/edit" 

try:
    # Extraemos el ID para probar de ambas formas
    sh = client.open_by_url(url_real)
    st.write(f"✅ ¡ÉXITO! Se pudo abrir el archivo: **{sh.title}**")
    
    st.subheader("4. Verificando pestañas")
    hojas = [h.title for h in sh.worksheets()]
    st.write(f"Hojas encontradas: {hojas}")
    
except Exception as e:
    st.error("❌ ERROR AL ABRIR EL ARCHIVO")
    st.info(f"Mensaje técnico del error: {e}")
    st.write("---")
    st.write("Si el error dice 'SpreadsheetNotFound' o 'PermissionDenied':")
    st.write(f"1. Copia este correo: `{info.get('client_email')}`")
    st.write("2. Ve a tu Google Sheet -> Compartir -> Pégalo y dale permiso de EDITOR.")
