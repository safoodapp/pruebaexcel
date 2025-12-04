import streamlit as st
import pandas as pd

st.title("Prueba de lectura desde Google Drive (Google Sheets)")

url = "https://docs.google.com/spreadsheets/d/1zbihxqDHWXHm1CKVuFH6pm8ADKyhaL5lTOLgfz8YUJ0/export?format=csv&gid=0"

try:
    df = pd.read_csv(url)
    st.success("Datos cargados correctamente")
    st.dataframe(df)
except Exception as e:
    st.error("Error al cargar la hoja")
    st.write(e)
