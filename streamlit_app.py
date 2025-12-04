import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from docxtpl import DocxTemplate
import base64
import os
import locale

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def generar_pdf_etiqueta(campos, nombre_archivo):
    c = canvas.Canvas(nombre_archivo, pagesize=A4)
    text = c.beginText(40, 800)
    text.setFont("Helvetica", 12)

    lineas = [
        f"Denominación comercial: {campos.get('denominacion_comercial', '')}",
        f"Nombre científico: {campos.get('nombre_cientifico', '')}",
        f"Ingredientes: {campos.get('ingredientes', '')}",
        f"Forma de captura: {campos.get('forma_captura', '')}",
        f"Zona de captura: {campos.get('zona_captura', '')}",
        f"País de origen: {campos.get('pais_origen', '')}",
        f"Arte de pesca: {campos.get('arte_pesca', '')}",
        f"Lote: {campos.get('lote', '')}",
        f"Fecha descongelación: {campos.get('fecha_descongelacion', '')}",
        f"Fecha caducidad: {campos.get('fecha_caducidad', '')}",
    ]

    for linea in lineas:
        text.textLine(linea)

    c.drawText(text)
    c.showPage()
    c.save()

# Configurar idioma del calendario (opcional)
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass

# Configurar página
st.set_page_config(page_title="Etiquetas de Santiago y Santiago", layout="centered")

# Mostrar portada
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False

if not st.session_state.mostrar_formulario:
    st.markdown("<h1 style='text-align:center;'>Etiquetas de Santiago y Santiago</h1>", unsafe_allow_html=True)
    if st.button("➕ Nueva etiqueta"):
        st.session_state.mostrar_formulario = True
    st.stop()

# Cargar datos desde Google Sheets
url = "https://docs.google.com/spreadsheets/d/1M-1zM8pxosv75N5gCtWaPkE1beQBOaMD/export?format=csv&gid=707739207"

try:
    df = pd.read_csv(url)
except Exception as e:
    st.error(f"Error al cargar datos desde Google Sheets: {e}")
    st.stop()


# Preparar opciones
def opciones_columna(col):
    try:
        lista = sorted([str(x) for x in df[col].dropna().unique() if isinstance(x, str)])
        return ["Selecciona una opción"] + lista
    except:
        return ["Selecciona una opción"]

productos = opciones_columna("denominacion_comercial")
formas = opciones_columna("forma_capturado")
zonas = opciones_columna("zona_captura")
paises = opciones_columna("pais_origen")
artes = opciones_columna("arte_pesca")

# Formulario
st.header("🧾 Crear nueva etiqueta")

producto = st.selectbox("Producto", productos)

if producto != "Selecciona una opción":
    fila = df[df["denominacion_comercial"] == producto].iloc[0]
    nombre_cientifico = fila.get("nombre_cientifico", "")
    ingredientes = fila.get("ingredientes", "")
    plantilla_nombre = str(fila.get("plantilla", "plantilla_etiqueta")).strip()
else:
    nombre_cientifico = ""
    ingredientes = ""
    plantilla_nombre = "plantilla_etiqueta"

st.text_input("Nombre científico", value=nombre_cientifico, disabled=True)
st.text_area("Ingredientes", value=ingredientes, disabled=True)

forma = st.radio("Forma de capturado", formas, horizontal=True)
zona = st.selectbox("Zona de captura", zonas)
pais = st.selectbox("País de origen", paises)
arte = st.selectbox("Arte de pesca", artes)

# ⬇️ Eliminado el campo 'peso'
lote = st.text_input("Lote")

usar_fecha_descongelacion = st.checkbox("¿Indicar fecha de descongelación?")
fecha_descongelacion = None
fecha_caducidad = None

if usar_fecha_descongelacion:
    fecha_descongelacion = st.date_input("Fecha de descongelación", format="DD/MM/YYYY")
    fecha_caducidad = fecha_descongelacion + timedelta(days=3)
    st.text_input("Fecha de caducidad", value=fecha_caducidad.strftime("%d/%m/%Y"), disabled=True)
else:
    fecha_caducidad = st.date_input("Fecha de caducidad (manual)", format="DD/MM/YYYY")

# Botón de generar
import streamlit as st
import pandas as pd
from datetime import datetime
from docx import Document
import base64
import copy

# Configurar página
st.set_page_config(page_title="Etiquetas", layout="centered")

# Cargar datos desde Google Sheets
url = "https://docs.google.com/spreadsheets/d/1M-1zM8pxosv75N5gCtWaPkE1beQBOaMD/export?format=csv&gid=707739207"
try:
    df = pd.read_csv(url)
except Exception as e:
    st.error(f"Error al cargar datos desde Google Sheets: {e}")
    st.stop()

# --- Formulario ---
st.header("Crear nueva etiqueta")

# Solo un selectbox de producto
productos = sorted(df["denominacion_comercial"].dropna().unique())
producto = st.selectbox("Producto", ["Selecciona un producto"] + list(productos))

if producto != "Selecciona un producto":
    fila = df[df["denominacion_comercial"] == producto].iloc[0]
    plantilla_path = fila.get("plantilla")  # plantilla correspondiente en repositorio

    # Rellenar automáticamente los campos del producto
    nombre_cientifico = fila.get("nombre_cientifico", "")
    ingredientes = fila.get("ingredientes", "")
    forma_captura = fila.get("forma_captura", "")
    zona_captura = fila.get("zona_captura", "")
    pais_origen = fila.get("pais_origen", "")
    arte_pesca = fila.get("arte_pesca", "")
    lote = fila.get("lote", "")

    st.text_input("Nombre científico", value=nombre_cientifico, disabled=True)
    st.text_area("Ingredientes", value=ingredientes, disabled=True)
    st.radio("Forma de capturado", options=["Selecciona una opción", "Capturado en agua dulce", "De cría (acuicultura)", "Capturado"], index=0, horizontal=True)
    st.selectbox("Zona de captura", options=["Selecciona una opción", "Zona 1", "Zona 2"])  # Ajusta según tus datos
    st.selectbox("País de origen", options=["Selecciona una opción", "España", "Portugal"])  # Ajusta según tus datos
    st.selectbox("Arte de pesca", options=["Selecciona una opción", "Red", "Anzuelo"])  # Ajusta según tus datos
    st.text_input("Lote", value=lote, disabled=True)

    # Fecha de caducidad (manual)
    st.date_input("Fecha de caducidad (manual)", value=datetime.now())

    # Número de etiquetas a generar
    num_copias = st.number_input("Número de etiquetas a generar", min_value=1, max_value=100, value=1, step=1)

    # --- Botón para generar ---
    if st.button("✅ Generar etiqueta"):
        # Abrir plantilla
        plantilla_doc = Document(plantilla_path)
        final_doc = Document()

        datos = {
            "denominacion_comercial": producto,
            "nombre_cientifico": nombre_cientifico,
            "ingredientes": ingredientes,
            "forma_captura": forma_captura,
            "zona_captura": zona_captura,
            "pais_origen": pais_origen,
            "arte_pesca": arte_pesca,
            "lote": lote,
            "fecha_descongelacion": "",
            "fecha_caducidad": ""
        }

        etiquetas_generadas = 0
        while etiquetas_generadas < num_copias:
            # Copiar la tabla de la plantilla
            base_table = plantilla_doc.tables[0]
            table_copy = copy.deepcopy(base_table._tbl)
            final_doc._body.append(table_copy)

            # Reemplazar los marcadores en la tabla recién copiada
            for row in final_doc.tables[-1].rows:
                for cell in row.cells:
                    for k, v in datos.items():
                        if f"{{{{{k}}}}}" in cell.text:
                            cell.text = cell.text.replace(f"{{{{{k}}}}}", str(v))

            etiquetas_generadas += 1

            # Salto de página cada 4 etiquetas
            if (etiquetas_generadas % 4 == 0) and (etiquetas_generadas < num_copias):
                final_doc.add_page_break()

        # Guardar Word final
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_docx = f"ETIQUETAS_{producto.replace(' ', '_')}_{timestamp}.docx"
        final_doc.save(output_docx)

        # Botón de descarga
        with open(output_docx, "rb") as f:
            b64_docx = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<a href="data:application/octet-stream;base64,{b64_docx}" download="{output_docx}">📥 Descargar etiquetas Word</a>',
                unsafe_allow_html=True
            )
