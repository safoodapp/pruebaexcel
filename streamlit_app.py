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
from datetime import datetime, timedelta
from docxtpl import DocxTemplate
import base64
import os

# Configurar página
st.set_page_config(page_title="Etiquetas de prueba", layout="centered")

# Subir plantilla Word
st.header("Selecciona tu plantilla")
plantilla_file = st.file_uploader("Sube tu plantilla Word (.docx)", type=["docx"])

if plantilla_file is not None:
    plantilla_path = "plantilla_temp.docx"
    with open(plantilla_path, "wb") as f:
        f.write(plantilla_file.read())

    # Cargar datos de prueba desde CSV de Google Sheets
    url = "https://docs.google.com/spreadsheets/d/tu_sheet/export?format=csv&gid=0"
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Error al cargar datos desde Google Sheets: {e}")
        st.stop()

    # Selección de producto
    productos = sorted(df["denominacion_comercial"].dropna().unique())
    producto = st.selectbox("Producto", ["Selecciona un producto"] + list(productos))

    if producto != "Selecciona un producto":
        fila = df[df["denominacion_comercial"] == producto].iloc[0]
        nombre_cientifico = fila.get("nombre_cientifico", "")
        ingredientes = fila.get("ingredientes", "")
        forma_captura = fila.get("forma_captura", "")
        zona_captura = fila.get("zona_captura", "")
        pais_origen = fila.get("pais_origen", "")
        arte_pesca = fila.get("arte_pesca", "")
        lote = fila.get("lote", "")

        # Número de etiquetas a generar
        num_copias = st.number_input("Número de etiquetas a generar", min_value=1, max_value=100, value=4, step=1)

        if st.button("✅ Generar etiquetas Word"):
            # Cargar plantilla
            doc = DocxTemplate(plantilla_path)

            etiquetas = []
            for i in range(num_copias):
                etiquetas.append({
                    "denominacion_comercial": producto,
                    "nombre_cientifico": nombre_cientifico,
                    "ingredientes": ingredientes,
                    "forma_captura": forma_captura,
                    "zona_captura": zona_captura,
                    "pais_origen": pais_origen,
                    "arte_pesca": arte_pesca,
                    "lote": lote,
                    "fecha_descongelacion": "",  # opcional, puedes añadir si la quieres
                    "fecha_caducidad": ""        # opcional
                })

            # Crear una lista de contextos, 4 etiquetas por página
            context_pages = [etiquetas[i:i+4] for i in range(0, len(etiquetas), 4)]

            # Generar documento final
            final_doc = DocxTemplate(plantilla_path)
            new_doc_path = f"ETIQUETAS_{producto.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

            # Insertar páginas
            from docx import Document
            final_doc_docx = Document(plantilla_path)
            for page_idx, page_context in enumerate(context_pages):
                if page_idx > 0:
                    # Agregar página nueva copiando la plantilla
                    for element in final_doc_docx.element.body:
                        final_doc_docx._body.append(element)
                # Reemplazar los marcadores de cada etiqueta en la página
                for idx, etiqueta in enumerate(page_context):
                    for k, v in etiqueta.items():
                        # Rellenar los marcadores con índice (1-4)
                        marcador = f"{{{{{k}}}}}"  # se puede ajustar si quieres indices
                        for p in final_doc_docx.paragraphs:
                            if marcador in p.text:
                                p.text = p.text.replace(marcador, str(v))

            final_doc_docx.save(new_doc_path)

            # Botón de descarga
            with open(new_doc_path, "rb") as file:
                b64_docx = base64.b64encode(file.read()).decode()
                st.markdown(
                    f'<a href="data:application/octet-stream;base64,{b64_docx}" download="{new_doc_path}">📥 Descargar etiquetas Word</a>',
                    unsafe_allow_html=True
                )
