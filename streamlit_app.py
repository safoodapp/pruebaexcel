import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from docxtpl import DocxTemplate
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

productos = opciones_columna("denominacion_comercial")
formas = opciones_columna("forma_capturado")
zonas = opciones_columna("zona_captura")
paises = opciones_columna("pais_origen")
artes = opciones_columna("arte_pesca")

# -------------------------------------------
# LISTAS NUEVAS: ESTADO Y ELABORACIONES
# -------------------------------------------

ESTADOS = ["Fresco", "Congelado", "Descongelado"]

ELABORACIONES = [
    "Entero",
    "Eviscerado",
    "Descabezado",
    "Pelado",
    "Limpio",
    "Troceado",
    "Desmigado",
    "Picado",
    "Trozos",
    "Tacos",
    "Migas",
    "Bocados",
    "Tiras",
    "Anillas",
    "Filetes",
    "Rodajas",
    "Medallones"
]

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

# -------------------------------------------
# RADIO: ESTADO DEL PRODUCTO
# -------------------------------------------

estado_producto = st.radio(
    "Estado del producto",
    ESTADOS,
    horizontal=True
)

# -------------------------------------------
# RADIO MULTICOLUMNA: ELABORACIÓN
# -------------------------------------------

st.subheader("Forma de preparación")

num_cols = 3
cols = st.columns(num_cols)

chunk_size = (len(ELABORACIONES) + num_cols - 1) // num_cols
chunks = [ELABORACIONES[i:i + chunk_size] for i in range(0, len(ELABORACIONES), chunk_size)]

seleccion = None

for idx, (col, opciones) in enumerate(zip(cols, chunks)):
    with col:
        elegido = st.radio("", [""] + opciones, key=f"prep_{idx}")
        if elegido != "":
            seleccion = elegido

forma_preparacion = seleccion

if not forma_preparacion:
    st.warning("Debes seleccionar una forma de preparación.")
    st.stop()

# -------------------------------------------
# REGLA C: GENERACIÓN DE DENOMINACIÓN FINAL
# -------------------------------------------

cortes = [
    "Filetes", "Rodajas", "Medallones", "Anillas",
    "Tacos", "Trozos", "Migas", "Bocados", "Tiras",
    "Desmigado", "Picado", "Troceado"
]

if forma_preparacion in cortes:
    denominacion_final = f"{forma_preparacion} de {producto}"
else:
    denominacion_final = f"{producto} {forma_preparacion.lower()}"

# -------------------------------------------
# CAPTURADO / ACUICULTURA
# -------------------------------------------

forma = st.radio("Forma de capturado / producción", formas, horizontal=True)

if "acui" in forma.lower():
    zona = ""
    arte = ""
    st.info("Producto de ACUICULTURA: no se aplica zona FAO ni arte de pesca.")
else:
    zona = st.selectbox("Zona de captura", zonas)
    arte = st.selectbox("Arte de pesca", artes)

pais = st.selectbox("País de origen", paises)

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

# -------------------------------------------
# BOTÓN GENERAR
# -------------------------------------------

if st.button("✅ Generar etiqueta"):

    campos = {
        "denominacion_comercial": producto,
        "denominacion_final": denominacion_final,
        "nombre_cientifico": nombre_cientifico,
        "ingredientes": ingredientes,
        "estado_producto": estado_producto,
        "forma_preparacion": forma_preparacion,
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
        "País de origen": pais,
        "Lote": lote
    }

    if "acui" not in forma.lower():
        campos_obligatorios["Zona de captura"] = zona
        campos_obligatorios["Arte de pesca"] = arte

    faltan = [k for k, v in campos_obligatorios.items() if not v or v == "Selecciona una opción"]

    if faltan:
        st.warning(f"Debes completar todos los campos obligatorios: {', '.join(faltan)}")
        st.stop()

    plantilla_path = f"{plantilla_nombre}.docx"

    if not os.path.exists(plantilla_path):
        st.error(f"No se encontró la plantilla: {plantilla_path}")
    else:
        doc = DocxTemplate(plantilla_path)
        doc.render(campos)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_docx = f"ETIQUETA_{producto.replace(' ', '_')}_{timestamp}.docx"
        doc.save(output_docx)

        with open(output_docx, "rb") as file:
            b64_docx = base64.b64encode(file.read()).decode()
            st.markdown(
                f'<a href="data:application/octet-stream;base64,{b64_docx}" download="{output_docx}">📥 Descargar etiqueta Word</a>',
                unsafe_allow_html=True
            )

        st.success("Etiqueta generada correctamente.")

