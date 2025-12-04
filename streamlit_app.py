import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from docxtpl import DocxTemplate
import base64
import os
import locale

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

    # Validación
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

    plantilla_path = f"{plantilla_nombre}.docx"
    if not os.path.exists(plantilla_path):
        st.error(f"No se encontró la plantilla: {plantilla_path}")
        st.stop()

    # -------------------------------
    #   RENDERIZAR PLANTILLA 1 VEZ
    # -------------------------------
    from docx import Document
    import copy
    from io import BytesIO

    doc_tpl = DocxTemplate(plantilla_path)
    doc_tpl.render(campos)

    # Guardar temporalmente para obtener el contenido ya renderizado
    temp_path = "temp_rendered.docx"
    doc_tpl.save(temp_path)

    # Cargar documento ya renderizado como Document normal
    plantilla_render = Document(temp_path)

    # Documento final donde colocaremos las 4 copias
    doc_final = Document()

    # -------------------------------
    #   DUPLICAR 4 COPIAS EN LA HOJA
    # -------------------------------
    for _ in range(4):
        for elem in plantilla_render.element.body:
            doc_final.element.body.append(copy.deepcopy(elem))
        doc_final.add_paragraph("")   # Espacio entre copias

    # Guardar resultado final
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_docx = f"ETIQUETASx4_{producto.replace(' ', '_')}_{timestamp}.docx"

    buffer = BytesIO()
    doc_final.save(buffer)
    buffer.seek(0)

    # Descargar archivo
    b64_docx = base64.b64encode(buffer.read()).decode()
    st.markdown(
        f'<a href="data:application/octet-stream;base64,{b64_docx}" download="{output_docx}">📥 Descargar etiqueta (4 copias en 1 hoja)</a>',
        unsafe_allow_html=True
    )

    st.success("Documento generado con 4 copias en la misma hoja 🎉")