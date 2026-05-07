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

forma = st.radio("Forma de capturado / producción", formas, horizontal=True)

# -------------------------------------------
# 🚨 LÓGICA ACUICULTURA vs CAPTURADO
# -------------------------------------------
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
# Usamos un contenedor para que los inputs no causen problemas de refresco
with st.container():
    col1, col2 = st.columns(2)
    for i in range(int(cantidad)):
        target_col = col1 if i % 2 == 0 else col2
        # El 'key' debe ser único para cada input, esto es vital en Streamlit
        p_neto = target_col.text_input(f"Peso neto etiqueta {i+1}", key=f"input_peso_{i}")
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

# -------------------------------------------
# 🚨 BOTÓN GENERAR
# -------------------------------------------
if st.button("✅ Generar etiquetas"):
    # Validación
    faltan = []
    if producto == "Selecciona una opción": faltan.append("Producto")
    if not lote: faltan.append("Lote")
    if pais == "Selecciona una opción": faltan.append("País de origen")
    
    if "acui" not in forma.lower():
        if zona == "Selecciona una opción": faltan.append("Zona de captura")
        if arte == "Selecciona una opción": faltan.append("Arte de pesca")
    
    # Validar pesos vacíos
    if any(not p.strip() for p in pesos_netos):
        st.error("⚠️ Debes rellenar todos los campos de Peso Neto.")
        st.stop()

    if faltan:
        st.warning(f"Campos obligatorios vacíos: {', '.join(faltan)}")
        st.stop()

    # Generación
    plantilla_path = f"{plantilla_nombre}.docx"
    if not os.path.exists(plantilla_path):
        st.error(f"Archivo de plantilla '{plantilla_path}' no encontrado.")
    else:
        for idx, peso in enumerate(pesos_netos):
            try:
                doc = DocxTemplate(plantilla_path)
                contexto = {
                    "denominacion_comercial": producto,
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
                
                nombre_limpio = producto.replace(" ", "_")
                output_name = f"ETIQUETA_{nombre_limpio}_{idx+1}.docx"
                doc.save(output_name)

                with open(output_name, "rb") as f:
                    data = f.read()
                    b64 = base64.b64encode(data).decode()
                    st.markdown(f'📥 **Etiqueta {idx+1} ({peso}):** <a href="data:application/octet-stream;base64,{b64}" download="{output_name}">Descargar Word</a>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error al generar la etiqueta {idx+1}: {e}")
                )

        st.info("Si necesitas PDF, ábrelo en Word o Google Docs y guárdalo como PDF.")
