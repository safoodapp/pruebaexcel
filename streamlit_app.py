import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from docxtpl import DocxTemplate
import base64
import os
import locale

# Intentar configurar idioma para fechas
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass

# Configurar página
st.set_page_config(page_title="Etiquetas Santiago y Santiago V2", layout="centered")

# Pantalla inicial
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False

if not st.session_state.mostrar_formulario:
    st.markdown("<h1 style='text-align:center;'>Etiquetas de Santiago y Santiago</h1>", unsafe_allow_html=True)
    if st.button("➕ Nueva etiqueta"):
        st.session_state.mostrar_formulario = True
    st.stop()

# --- CARGAR DATOS (NUEVA URL GOOGLE SHEETS) ---
# He actualizado la URL a la que mencionaste
url = "https://docs.google.com/spreadsheets/d/1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA/edit?gid=57656075#gid=57656075"

try:
    df = pd.read_csv(url)
except Exception as e:
    st.error(f"Error al cargar datos desde Google Sheets: {e}")
    st.stop()

# Preparar listas desplegables
def opciones_columna(col):
    try:
        lista = sorted([str(x) for x in df[col].dropna().unique() if isinstance(x, str)])
        return ["Selecciona una opción"] + lista
    except:
        return ["Selecciona una opción"]

productos = opciones_columna("denominacion_comercial")
zonas = opciones_columna("zona_captura")
paises = opciones_columna("pais_origen")
artes = opciones_columna("arte_pesca")
formas_metodo = opciones_columna("forma_capturado") # Método de pesca

# --- FORMULARIO ---
st.header("🧾 Crear nueva etiqueta")

# 1. Selección de Producto
producto_sel = st.selectbox("Producto", productos)

if producto_sel != "Selecciona una opción":
    fila = df[df["denominacion_comercial"] == producto_sel].iloc[0]
    nombre_cientifico = fila.get("nombre_cientifico", "")
    ingredientes = fila.get("ingredientes", "")
    pueden_contener = fila.get("alergenos", "") # O "PUEDE_CONTENER" según tu Excel
else:
    nombre_cientifico = ""
    ingredientes = ""
    pueden_contener = ""

st.text_input("Nombre científico", value=nombre_cientifico, disabled=True)
st.text_area("Ingredientes", value=ingredientes, disabled=True)
st.text_input("Puede contener trazas de", value=pueden_contener)

# 2. SELECTORES NUEVOS (Estado, Transformación, Fechas)
col1, col2 = st.columns(2)

with col1:
    estado_prod = st.selectbox("Estado del producto (Define plantilla)", ["CONGELADO", "FRESCO", "DESCONGELADO"])
    forma_trans = st.text_input("Forma de transformación", placeholder="Ej: Eviscerado, Fileteado...")

with col2:
    fecha_elab = st.date_input("Fecha de elaboración", format="DD/MM/YYYY")
    lote = st.text_input("Lote")

# 3. Datos de Origen
forma_pesca = st.radio("Método de producción/pesca", formas_metodo, horizontal=True)

if "acui" in forma_pesca.lower():
    zona = "N/A"
    arte = "N/A"
    st.info("Producto de ACUICULTURA: No requiere Zona FAO ni Arte de pesca.")
else:
    zona = st.selectbox("Zona de captura", zonas)
    arte = st.selectbox("Arte de pesca", artes)

pais = st.selectbox("País de origen", paises)

# 4. Lógica de Caducidad
usar_descongelacion = st.checkbox("¿Es un producto descongelado? (Suma 3 días a caducidad)")
if usar_descongelacion:
    fecha_cad = fecha_elab + timedelta(days=3)
    st.info(f"Caducidad calculada: {fecha_cad.strftime('%d/%m/%Y')}")
else:
    fecha_cad = st.date_input("Fecha de caducidad", format="DD/MM/YYYY")

# --- BOTÓN GENERAR ---
if st.button("✅ Generar etiqueta"):

    # Mapeo de datos para la plantilla Word
    campos = {
        "DENOMINACION_COMERCIAL": producto_sel.upper(),
        "nombre_cientifico": nombre_cientifico,
        "forma_transformacion": forma_trans,
        "ingredientes": ingredientes,
        "PUEDE_CONTENER": pueden_contener,
        "pais_origen": pais,
        "zona_captura": zona,
        "arte_pesca": arte,
        "forma_captura": forma_pesca,
        "estados_productos": estado_prod,
        "lote": lote,
        "fecha_elaboracion": fecha_elab.strftime("%d/%m/%Y"),
        "fecha_caducidad": fecha_cad.strftime("%d/%m/%Y")
    }

    # Selección de plantilla dinámica
    nombre_plantilla = f"FT PRODUCTO {estado_prod}.docx"
    
    if not os.path.exists(nombre_plantilla):
        st.error(f"Error: No se encuentra el archivo de plantilla '{nombre_plantilla}'")
    elif producto_sel == "Selecciona una opción" or not lote:
        st.warning("Por favor, selecciona un producto e introduce un lote.")
    else:
        # Renderizar el documento
        doc = DocxTemplate(nombre_plantilla)
        doc.render(campos)

        # Guardar y ofrecer descarga
        timestamp = datetime.now().strftime('%H%M%S')
        nombre_archivo = f"ETIQUETA_{estado_prod}_{timestamp}.docx"
        doc.save(nombre_archivo)

        with open(nombre_archivo, "rb") as f:
            base64_docx = base64.b64encode(f.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{base64_docx}" download="{nombre_archivo}" style="text-decoration:none; border:2px solid #4CAF50; padding:10px; border-radius:5px; color:white; background-color:#4CAF50;">📥 Descargar Etiqueta {estado_prod}</a>'
            st.markdown(href, unsafe_allow_html=True)
        
        st.success(f"Etiqueta para producto {estado_prod} generada con éxito.")
