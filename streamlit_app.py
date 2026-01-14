import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF
import io

st.set_page_config(page_title="Etiquetas Pescado PRO", layout="centered")

# =========================================================
# CONFIGURACIÓN GOOGLE SHEETS
# =========================================================
SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"

GIDS = {
    "PRODUCTOS": "0",
    "FORMAS_TRANSFORMACION": "1141842769",
    "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476",
    "ZONAS_FAO": "907306114",
    "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266",
    "TRAZAS_CONFIG": "1059656739",
}

def load_sheet(name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GIDS[name]}"
    return pd.read_csv(url)

# Función para añadir la opción por defecto a las listas
def preparar_lista(df, col_idx=None, col_name=None):
    if col_name:
        items = df[col_name].dropna().unique().tolist()
    else:
        items = df.iloc[:, col_idx].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

# =========================================================
# FUNCIÓN GENERADORA DE PDF
# =========================================================
def generar_pdf_a4(datos, cantidad):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    ancho_et, alto_et = 95, 90
    mx, my = 7, 10
    curr_x, curr_y = mx, my

    for i in range(cantidad):
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # Bloque 1: Cabecera
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(curr_x, curr_y, ancho_et, 16, 'F')
        pdf.rect(curr_x, curr_y, ancho_et, 16)
        pdf.set_xy(curr_x, curr_y + 2)
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(ancho_et, 5, str(datos['nombre_comercial']).upper(), align='C')
        pdf.set_xy(curr_x, curr_y + 11)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C')

        # Bloque 2: Alérgenos
        pdf.rect(curr_x, curr_y + 16, ancho_et, 12)
        pdf.set_font("Arial", 'B', 7)
        pdf.set_xy(curr_x + 2, curr_y + 17)
        pdf.multi_cell(ancho_et - 4, 3, str(datos['alergenos']).upper())

        # Bloque 3: Datos de Origen (Solo si existen)
        pdf.rect(curr_x, curr_y + 28, ancho_et, 18)
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(curr_x + 5, curr_y + 30)
        if datos['zona']:
            pdf.cell(0, 4, f"- ZONA: {datos['zona']}")
        pdf.set_xy(curr_x + 5, curr_y + 34)
        pdf.cell(0, 4, f"- METODO: {datos['metodo']}")
        pdf.set_xy(curr_x + 5, curr_y + 38)
        if datos['arte']:
            pdf.cell(0, 4, f"- ARTE DE PESCA: {datos['arte']}")

        # Bloque 4: Estado
        pdf.rect(curr_x, curr_y + 46, ancho_et, 10)
        pdf.set_xy(curr_x, curr_y + 47)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(ancho_et, 4, f"PRODUCTO {str(datos['estado']).upper()}", align='C', ln=True)
        pdf.set_font("Arial", '', 7)
        pdf.set_x(curr_x)
        pdf.cell(ancho_et, 3, "COCINAR COMPLETAMENTE ANTES DE CONSUMIR", align='C')

        # Bloque 5: Trazabilidad
        pdf.rect(curr_x, curr_y + 56, ancho_et, 18)
        pdf.set_xy(curr_x + 5, curr_y + 58)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 4, f"LOTE: {datos['lote']}")
        pdf.set_font("Arial", '', 8)
        if datos['f_descong']:
            pdf.set_xy(curr_x + 5, curr_y + 63)
            pdf.cell(0, 4, f"F. DESCONGELACION: {datos['f_descong']}")
        pdf.set_xy(curr_x + 5, curr_y + 67)
        pdf.cell(0, 4, f"F. CADUCIDAD: {datos['f_cad']}")

        # Bloque 6: Expedidor y Óvalo
        pdf.rect(curr_x, curr_y + 74, ancho_et, 16)
        pdf.set_font("Arial", '', 6)
        pdf.set_xy(curr_x + 2, curr_y + 76)
        pdf.multi_cell(ancho_et - 30, 3, f"{datos['expedidor']}\nCalle Laguna del Marquesado 43C, Nave 43C\n28021 Madrid")
        
        pdf.ellipse(curr_x + 68, curr_y + 76, 22, 12)
        pdf.set_xy(curr_x + 68, curr_y + 78)
        pdf.set_font("Arial", 'B', 6)
        pdf.cell(22, 3, "ES", align='C', ln=True)
        pdf.set_xy(curr_x + 68, curr_y + 80)
        pdf.cell(22, 3, str(datos['ovalo']), align='C', ln=True)
        pdf.set_xy(curr_x + 68, curr_y + 82)
        pdf.cell(22, 3, "CE", align='C')

        if (i + 1) % 2 == 0:
            curr_x = mx
            curr_y += alto_et + 5
        else:
            curr_x += ancho_et + 5
        if (i + 1) % 6 == 0 and (i + 1) < cantidad:
            pdf.add_page()
            curr_x, curr_y = mx, my
            
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# CARGA DE DATOS
# =========================================================
df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_exped = load_sheet("EXPEDIDORES")
df_trazas = load_sheet("TRAZAS_CONFIG")

# =========================================================
# INTERFAZ STREAMLIT
# =========================================================
st.title("Generador Profesional de Etiquetas")

col1, col2 = st.columns(2)
with col1:
    nombre_base = st.selectbox("Producto", preparar_lista(df_productos, col_name="NOMBRE_BASE"))
    forma = st.selectbox("Transformación", preparar_lista(df_transform, col_idx=0))
    estado = st.selectbox("Estado", preparar_lista(df_estados, col_idx=0))
    lote = st.text_input("Número de Lote", placeholder="Ej: L26006")
with col2:
    metodo = st.selectbox("Producción", preparar_lista(df_metodo, col_idx=0))
    fecha_cad = st.date_input("Caducidad", value=date.today())
    cantidad = st.number_input("Cantidad de etiquetas", min_value=1, value=1)
    expedidor = st.selectbox("Expedidor", preparar_lista(df_exped, col_name="EXPEDIDOR"))

# Variables condicionales (Zona y Arte solo si es Capturado)
zona = arte = None
if "Capturado" in metodo:
    c3, c4 = st.columns(2)
    with c3: zona = st.selectbox("Zona FAO", preparar_lista(df_zonas, col_idx=0))
    with c4: arte = st.selectbox("Arte", preparar_lista(df_artes, col_idx=0))

# Fecha descongelación obligatoria solo si el estado es descongelado
fecha_descong = None
if estado.upper() == "DESCONGELADO":
    fecha_descong = st.date_input("Fecha de Descongelación")

# =========================================================
# VALIDACIÓN Y BOTÓN
# =========================================================
st.divider()

# Lista de validación
errores = []
if "Selecciona una opción" in [nombre_base, forma, estado, metodo, expedidor]:
    errores.append("Faltan selectores por elegir.")
if not lote.strip():
    errores.append("El Lote es obligatorio.")
if "Capturado" in metodo and ("Selecciona una opción" in [str(zona), str(arte)]):
    errores.append("Faltan datos de Zona o Arte para pesca capturada.")

if errores:
    st.warning("⚠️ " + " | ".join(errores))
    st.button("🚀 GENERAR ETIQUETAS", disabled=True)
else:
    # Si todo está OK, preparamos datos y mostramos el botón
    producto_data = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
    nombre_comercial = f"{nombre_base} {forma} {estado}"
    ovalo = df_exped[df_exped["EXPEDIDOR"] == expedidor]["OVALO_SANITARIO"].iloc[0]
    texto_alergenos = f"Contiene {producto_data['ALERGENOS']}. Puede contener {df_trazas['PUEDE_CONTENER'].iloc[0]}."

    if st.button("🚀 GENERAR ETIQUETAS"):
        info_final = {
            "nombre_comercial": nombre_comercial,
            "nombre_cientifico": producto_data["NOMBRE_CIENTIFICO"],
            "alergenos": texto_alergenos,
            "metodo": metodo,
            "zona": zona if zona != "Selecciona una opción" else None,
            "arte": arte if arte != "Selecciona una opción" else None,
            "estado": estado,
            "lote": lote,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "f_descong": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "expedidor": expedidor,
            "ovalo": ovalo
        }
        
        pdf_res = generar_pdf_a4(info_final, cantidad)
        st.download_button(
            label="📥 DESCARGAR PDF PARA IMPRIMIR",
            data=pdf_res,
            file_name=f"etiquetas_{lote}.pdf",
            mime="application/pdf"
        )