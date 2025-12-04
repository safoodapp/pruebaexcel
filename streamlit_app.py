import streamlit as st
import pandas as pd

st.title("Prueba de lectura desde Google Drive (Google Sheets)")

url = "AQUI_PONDRÁS_TU_ENLACE_CSV"

try:
    df = pd.read_csv(url)
    st.success("Datos cargados correctamente")
    st.dataframe(df)
except Exception as e:
    st.error("Error al cargar la hoja")
    st.write(e)
