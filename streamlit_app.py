import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from docxtpl import DocxTemplate
import os

st.set_page_config(page_title="Etiquetas Santiago y Santiago", layout="centered")

# --- NUEVO LINK (FORMATO EXCEL PARA LEER TODO) ---
URL_EXCEL = "https://docs.google.com/spreadsheets/d/1M-1zM8pxosv75N5gCtWaPkE1beQBOaMD/export?format=xlsx"

@st.cache_data(ttl=60)
def cargar_todo_el_excel(url):
    try:
        # sheet_name=None carga TODAS las pestañas en un diccionario
        dict_hojas = pd.read_excel(url, sheet_name=None)
        return dict_hojas
    except Exception as e:
        st.error(f"Error al leer el Excel completo: {e}")
        return None

hojas = cargar_todo_el_excel(URL_EXCEL)

if hojas:
    # 1. Elegimos qué pestaña usar para cada cosa
    # Asegúrate de que los nombres de las pestañas en tu Excel coincidan aquí
    df_productos = hojas.get("DATOS", list(hojas.values())[0]) # Coge la pestaña 'DATOS' o la primera que encuentre
    
    # Limpiar nombres de columnas
    df_productos.columns = df_productos.columns.str.strip()

    # --- FORMULARIO ---
    st.header("🧾 Generador de Etiquetas")

    # Selector de producto (de la pestaña de productos)
    lista_prod = ["Selecciona uno"] + sorted(df_productos["denominacion_comercial"].dropna().unique().tolist())
    producto_sel = st.selectbox("Producto", lista_prod)

    if producto_sel != "Selecciona uno":
        fila = df_productos[df_productos["denominacion_comercial"] == producto_sel].iloc[0]
        
        # 2. Rellenamos datos automáticamente
        nombre_cientifico = fila.get("nombre_cientifico", "")
        ingredientes = fila.get("ingredientes", "")
        alergenos = fila.get("alergenos", "")

        st.text_input("Nombre científico", value=nombre_cientifico, disabled=True)
        st.text_area("Ingredientes", value=ingredientes, disabled=True)
        contener_input = st.text_input("Puede contener trazas de", value=alergenos)

        # 3. Selectores de Estado y Transformación
        col1, col2 = st.columns(2)
        with col1:
            estado_prod = st.selectbox("Estado del producto", ["CONGELADO", "FRESCO", "DESCONGELADO"])
            forma_trans = st.text_input("Forma de transformación")
        with col2:
            fecha_elab = st.date_input("Fecha de elaboración", format="DD/MM/YYYY")
            lote = st.text_input("Lote")

        # 4. Origen (aquí podrías usar datos de OTRAS pestañas si quisieras)
        # Por ahora lo dejamos manual o con listas simples
        pais = st.text_input("País de origen", value=fila.get("pais_origen", ""))
        zona = st.text_input("Zona de captura", value=fila.get("zona_captura", ""))
        arte = st.text_input("Arte de pesca", value=fila.get("arte_pesca", ""))
        metodo = st.selectbox("Método de producción", ["Extractiva", "Acuicultura"])

        # Lógica de Caducidad
        if estado_prod == "DESCONGELADO":
            fecha_cad = fecha_elab + timedelta(days=3)
        else:
            fecha_cad = st.date_input("Fecha de caducidad", format="DD/MM/YYYY")

        # --- BOTÓN GENERAR ---
        if st.button("✅ GENERAR ETIQUETA"):
            nombre_plantilla = f"FT PRODUCTO {estado_prod}.docx"
            
            if os.path.exists(nombre_plantilla):
                doc = DocxTemplate(nombre_plantilla)
                contexto = {
                    "DENOMINACION_COMERCIAL": str(producto_sel).upper(),
                    "nombre_cientifico": nombre_cientifico,
                    "lforma_transformacion": forma_trans,
                    "ingredientes": ingredientes,
                    "PUEDE_CONTENER": contener_input,
                    "pais_origen": pais,
                    "zona_captura": zona,
                    "arte_pesca": arte,
                    "forma_captura": metodo,
                    "estados_productos": estado_prod,
                    "lote": lote,
                    "fecha_elaboracion": fecha_elab.strftime("%d/%m/%Y"),
                    "fecha_caducidad": fecha_cad.strftime("%d/%m/%Y")
                }
                doc.render(contexto)
                out = f"ETIQUETA_{lote}.docx"
                doc.save(out)
                
                with open(out, "rb") as f:
                    st.download_button("📥 Descargar Word", f, file_name=out)
            else:
                st.error(f"Sube la plantilla {nombre_plantilla} a GitHub")
