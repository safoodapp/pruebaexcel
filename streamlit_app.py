import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from docxtpl import DocxTemplate
from docx import Document
from docxcompose.composer import Composer
import base64
import os
import locale

# Configurar idioma
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass

# Configurar página
st.set_page_config(page_title="Etiquetas de Santiago y Santiago", layout="centered")

# Pantalla inicial
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

# Preparar listas
def opciones_columna(col):
    try:
        lista = sorted([str(x) for x in df[col].dropna().unique() if isinstance(x, str)])
        return ["Selecciona una opción"] + lista
    except:
        return ["Selecciona una opción"]

productos = opciones_columna("DENOMINACION_COMERCIAL")
formas = opciones_columna("forma_capturado")
zonas = opciones_columna("zona_captura")
paises = opciones_columna("pais_origen")
artes = opciones_columna("arte_pesca")

# Formulario
st.header("🧾 Crear nueva etiqueta")

producto = st.selectbox("Producto", productos)

if producto != "Selecciona una opción":
    fila = df[df["DENOMINACION_COMERCIAL"] == producto].iloc[0]
    nombre_cientifico = fila.get("nombre_cientifico", "")
    ingredientes = fila.get("ingredientes", "")
    plantilla_nombre = str(fila.get("plantilla", "")).strip()
else:
    nombre_cientifico = ""
    ingredientes = ""
    plantilla_nombre = ""

st.text_input("Nombre científico", value=nombre_cientifico, disabled=True)
st.text_area("Ingredientes", value=ingredientes, disabled=True)

forma = st.radio("Forma de capturado / producción", formas, horizontal=True)

zona = ""
arte = ""
if "acui" in forma.lower():
    st.info("Producto de ACUICULTURA: no se aplica zona FAO ni arte de pesca.")
else:
    zona = st.selectbox("Zona de captura", zonas)
    arte = st.selectbox("Arte de pesca", artes)

pais = st.selectbox("País de origen", paises)
lote = st.text_input("Lote")

# --- SECCIÓN DE CANTIDAD Y PESOS ---
st.subheader("Configuración de Impresión")
cantidad = st.number_input("¿Cuántas etiquetas quieres sacar?", min_value=1, max_value=50, value=1, step=1)

pesos_netos = []
with st.container():
    col1, col2 = st.columns(2)
    for i in range(int(cantidad)):
        t_col = col1 if i % 2 == 0 else col2
        p_neto = t_col.text_input(f"Peso neto etiqueta {i+1}", key=f"p_{i}")
        pesos_netos.append(p_neto)

usar_fecha_descongelacion = st.checkbox("¿Indicar fecha de descongelación?")
fecha_descongelacion = None
fecha_caducidad = None

if usar_fecha_descongelacion:
    fecha_descongelacion = st.date_input("Fecha de descongelación", format="DD/MM/YYYY")
    fecha_caducidad = fecha_descongelacion + timedelta(days=3)
    st.text_input("Fecha de caducidad", value=fecha_caducidad.strftime("%d/%m/%Y"), disabled=True)
else:
    fecha_caducidad = st.date_input("Fecha de caducidad (manual)", format="DD/MM/YYYY")

# --- BOTÓN GENERAR ---
if st.button("✅ Generar Archivo Único"):
    if producto == "Selecciona una opción" or not lote:
        st.error("Por favor, selecciona un producto e indica el lote.")
        st.stop()
    
    if any(not p.strip() for p in pesos_netos):
        st.error("Debes rellenar el peso neto de todas las etiquetas.")
        st.stop()

    posibles_nombres = [f"{plantilla_nombre}.docx", plantilla_nombre]
    ruta_plantilla = None
    for p in posibles_nombres:
        if os.path.exists(p):
            ruta_plantilla = p
            break

    if not ruta_plantilla:
        st.error(f"No se encuentra la plantilla: {plantilla_nombre}")
        st.stop()

    try:
        # Lista para guardar los archivos temporales
        archivos_temporales = []

        for idx, peso in enumerate(pesos_netos):
            doc = DocxTemplate(ruta_plantilla)
            contexto = {
                "DENOMINACION_COMERCIAL": producto,
                "nombre_cientifico": nombre_cientifico,
                "ingredientes": ingredientes,
                "forma_captura": forma,
                "zona_captura": zona,
                "pais_origen": pais,
                "arte_pesca": arte,
                "lote": lote,
                "peso_neto": peso,
                "fecha_descongelacion": fecha_descongelacion.strftime("%d/%m/%Y") if fecha_descongelacion else "",
                "fecha_caducidad": fecha_caducidad.strftime("%d/%m/%Y") if fecha_caducidad else ""
            }
            doc.render(contexto)
            temp_name = f"temp_{idx}.docx"
            doc.save(temp_name)
            archivos_temporales.append(temp_name)

        # Unir todos los archivos en uno solo
        master = Document(archivos_temporales[0])
        composer = Composer(master)

        for i in range(1, len(archivos_temporales)):
            doc_temp = Document(archivos_temporales[i])
            composer.append(doc_temp)

        # Nombre del archivo con el NÚMERO DE LOTE
        nombre_final = f"ETIQUETAS_LOTE_{lote}.docx"
        composer.save(nombre_final)

        # Ofrecer descarga
        with open(nombre_final, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.success(f"¡Hecho! Se han agrupado {len(pesos_netos)} etiquetas.")
            st.markdown(f'📥 <a href="data:application/octet-stream;base64,{b64}" download="{nombre_final}">Descargar archivo único (Lote: {lote})</a>', unsafe_allow_html=True)

        # Limpiar archivos temporales
        for temp in archivos_temporales:
            os.remove(temp)

    except Exception as e:
        st.error(f"Error al agrupar las etiquetas: {e}")
