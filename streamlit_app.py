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
from docx2pdf import convert

# Número de etiquetas a generar
num_copias = st.selectbox("Número de etiquetas a generar", [1,2,3,4], index=2)

if st.button("✅ Generar etiqueta"):
    campos = {
        "denominacion_comercial": producto,
        "nombre_cientifico": nombre_cientifico,
        "ingredientes": ingredientes,
        "forma_captura": forma,
        "zona_captura": zona,
        "pais_origen": pais,
        "arte_pesca": arte,
        "lote": lote,
        "fecha_descongelacion": fecha_descongelacion.strftime("%d/%m/%Y") if fecha_descongelacion else "",
        "fecha_caducidad": fecha_caducidad.strftime("%d/%m/%Y") if fecha_caducidad else ""
    }

    # Validación de campos obligatorios
    campos_obligatorios = {
        "Producto": producto,
        "Forma de captura": forma,
        "Zona de captura": zona,
        "País de origen": pais,
        "Arte de pesca": arte,
        "Lote": lote
    }
    faltan = [k for k, v in campos_obligatorios.items() if not v or v == "Selecciona una opción"]
    if faltan:
        st.warning(f"Debes completar todos los campos obligatorios: {', '.join(faltan)}")
        st.stop()

    # Cargar plantilla Word
    plantilla_path = f"{plantilla_nombre}.docx"
    if not os.path.exists(plantilla_path):
        st.error(f"No se encontró la plantilla: {plantilla_path}")
        st.stop()

    doc = DocxTemplate(plantilla_path)

    # Preparar campos para las N copias
    # Suponemos que la plantilla tiene 4 marcadores independientes:
    # den_comercial_1, den_comercial_2, ..., forma_captura_1, ...
    render_data = {}
    for i in range(1, num_copias+1):
        for k, v in campos.items():
            render_data[f"{k}_{i}"] = v

    doc.render(render_data)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_docx = f"ETIQUETA_{producto.replace(' ', '_')}_{timestamp}.docx"
    doc.save(output_docx)

    # Descargar Word
    with open(output_docx, "rb") as file:
        b64_docx = base64.b64encode(file.read()).decode()
        st.markdown(
            f'<a href="data:application/octet-stream;base64,{b64_docx}" download="{output_docx}">📥 Descargar etiqueta Word</a>',
            unsafe_allow_html=True
        )

    # Convertir a PDF automáticamente usando docx2pdf
    output_pdf = output_docx.replace(".docx", ".pdf")
    convert(output_docx, output_pdf)

    # Descargar PDF
    with open(output_pdf, "rb") as f:
        b64_pdf = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<a href="data:application/pdf;base64,{b64_pdf}" download="{output_pdf}">🧾 Descargar etiqueta en PDF</a>',
            unsafe_allow_html=True
        )
