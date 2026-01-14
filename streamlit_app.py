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

# =========================================================
# FUNCIÓN GENERADORA DE PDF (DISEÑO SEGÚN MOKUP)
# =========================================================
def generar_pdf_a4(datos, cantidad):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    # Configuración de cuadrícula (2 columnas x 3 filas = 6 etiquetas por A4)
    ancho_et, alto_et = 95, 90
    mx, my = 7, 10
    x, y = mx, my

    for i in range(cantidad):
        # Dibujar recuadro y secciones
        pdf.rect(x, y, ancho_et, alto_et)
        
        # Bloque 1: Nombre Comercial y Científico
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(x, y, ancho_et, 16, 'F')
        pdf.rect(x, y, ancho_et, 16)
        pdf.set_xy(x, y + 2)
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(ancho_et, 5, datos['nombre_comercial'].upper(), align='C')
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C')

        # Bloque 2: Ingredientes y Alérgenos
        pdf.rect(x, y + 16, ancho_et, 12)
        pdf.set_font("Arial", 'B', 7)
        pdf.set_xy(x + 2, y + 17)
        pdf.multi_cell(ancho_et - 4, 3, datos['alergenos'].upper())

        # Bloque 3: Datos de Origen
        pdf.rect(x, y + 28, ancho_et, 18)
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(x + 5, y + 30)
        pdf.cell(0, 4, f"- ZONA: {datos['zona'] or 'N/A'}", ln=True)
        pdf.set_xy(x + 5, y + 34)
        pdf.cell(0, 4, f"- MÉTODO: {datos['metodo']}", ln=True)
        pdf.set_xy(x + 5, y + 38)
        pdf.cell(0, 4, f"- ARTE DE PESCA: {datos['arte'] or 'N/A'}", ln=True)

        # Bloque 4: Estado y Advertencia
        pdf.rect(x, y + 46, ancho_et, 10)
        pdf.set_font("Arial", 'B', 8)
        pdf.set_xy(x, y + 47)
        pdf.cell(ancho_et, 4, f"PRODUCTO {datos['estado'].upper()}", align='C', ln=True)
        pdf.set_font("Arial", '', 7)
        pdf.cell(ancho_et, 3, "COCINAR COMPLETAMENTE ANTES DE CONSUMIR", align='C')

        # Bloque 5: Lote y Fechas
        pdf.rect(x, y + 56, ancho_et, 18)
        pdf.set_font("Arial", 'B', 9)
        pdf.set_xy(x + 5, y + 58)
        pdf.cell(0, 4, f"LOTE: {datos['lote']}", ln=True)
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(x + 5, y + 63)
        if datos['f_descong']: pdf.cell(0, 4, f"F. DESCONGELACIÓN: {datos['f_descong']}", ln=True)
        pdf.set_xy(x + 5, y + 67)
        pdf.cell(0, 4, f"F. CADUCIDAD: {datos['f_cad']}", ln=True)

        # Bloque 6: Expedidor y Óvalo (Diseño fiel al esquema)
        pdf.rect(x, y + 74, ancho_et, 16)
        pdf.set_font("Arial", '', 6)
        pdf.set_xy(x + 2, y + 76)
        pdf.multi_cell(ancho_et - 30, 3, f"{datos['expedidor']}\nCalle Laguna del Marquesado 43C\n28021 Madrid")
        
        # Óvalo Sanitario
        pdf.ellipse(x + 68, y + 76, 22, 12)
        pdf.set_xy(x + 68, y + 78)
        pdf.set_font("Arial", 'B', 6)
        pdf.cell(22, 3, "ES", align='C', ln=True)
        pdf.set_xy(x + 68, y + 80)
        pdf.cell(22, 3, datos['ovalo'], align='C', ln=True)
        pdf.set_xy(x + 68, y + 82)
        pdf.cell(22, 3, "CE", align='C')

        # Lógica de posición
        if (i + 1) % 2 == 0:
            x = mx
            y += alto_et + 5
        else:
            x += ancho_et + 5
        if (i + 1) % 6 == 0 and (i + 1) < cantidad:
            pdf.add_page()
            x, y = mx, my
            
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# CARGA DE DATOS Y APP
# =========================================================
df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_exped = load_sheet("EXPEDIDORES")
df_trazas = load_sheet("TRAZAS_CONFIG")

st.title("Generador Profesional de Etiquetas")

# Formulario
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        nombre_base = st.selectbox("Producto", df_productos["NOMBRE_BASE"].unique())
        forma = st.selectbox("Transformación", df_transform.iloc[:, 0].unique())
        estado = st.selectbox("Estado", df_estados.iloc[:, 0].unique())
        lote = st.text_input("Número de Lote", placeholder="Ej: L26006")
    
    with col2:
        metodo = st.selectbox("Producción", df_metodo.iloc[:, 0].unique())
        fecha_cad = st.date_input("Caducidad", value=date.today())
        cantidad = st.number_input("Cantidad de etiquetas", min_value=1, value=1)
        expedidor = st.selectbox("Expedidor", df_exped["EXPEDIDOR"].unique())

# Variables automáticas
producto = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
nombre_comercial = f"{nombre_base} {forma} {estado}"
ovalo = df_exped[df_exped["EXPEDIDOR"] == expedidor]["OVALO_SANITARIO"].iloc[0]
texto_alergenos = f"Contiene {producto['ALERGENOS']}. Puede contener {df_trazas['PUEDE_CONTENER'].iloc[0]}."

# Origen condicional
zona = arte = None
if metodo == "Capturado":
    c3, c4 = st.columns(2)
    with c3: zona = st.selectbox("Zona FAO", df_zonas.iloc[:, 0].unique())
    with c4: arte = st.selectbox("Arte", df_artes.iloc[:, 0].unique())

fecha_descong = st.date_input("F. Descongelación") if estado == "descongelado" else None

# =========================================================
# GENERACIÓN FINAL
# =========================================
st.divider()

if st.button("🚀 GENERAR ETIQUETAS"):
    if not lote:
        st.error("Es obligatorio introducir un número de lote.")
    else:
        datos_etiqueta = {
            "nombre_comercial": nombre_comercial,
            "nombre_cientifico": producto["NOMBRE_CIENTIFICO"],
            "alergenos": texto_alergenos,
            "metodo": metodo,
            "zona": zona,
            "arte": arte,
            "estado": estado,
            "lote": lote,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "f_descong": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "expedidor": expedidor,
            "ovalo": ovalo
        }
        
        pdf_res = generar_pdf_a4(datos_etiqueta, cantidad)
        
        st.success(f"¡Etiquetas listas! Se han generado {cantidad} unidades.")
        st.download_button(
            label="📥 DESCARGAR PDF PARA IMPRIMIR",
            data=pdf_res,
            file_name=f"etiquetas_{lote}.pdf",
            mime="application/pdf"
        )