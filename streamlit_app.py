import streamlit as st
import pandas as pd

st.title("PRUEBA CON LA HOJA REAL")

url = "https://docs.google.com/spreadsheets/d/1M-1zM8pxosv75N5gCtWaPkE1beQBOaMD/export?format=csv&gid=707739207"

try:
    df = pd.read_csv(url)
    st.success("Hoja REAL cargada correctamente")
    st.dataframe(df)
except Exception as e:
    st.error("Error cargando la hoja REAL")
    st.write(e)
