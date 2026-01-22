import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF
import io

st.set_page_config(page_title="Etiquetas Pescado PRO - RD 1082/2025", layout="centered")

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

def preparar_lista(df, col_idx=None, col_name=None):
    if col_name:
        items = df[col_name].dropna().unique().tolist()
    else:
        items = df.iloc[:, col_idx].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

# --- LÓGICA DE CONCORDANCIA DE GÉNERO ---
def ajustar_genero(texto, genero):
    if genero == "F":
        return texto.replace("o ", "a ").replace("ado", "ada")
    return texto

# =========================================================
# FUNCIÓN GENERADORA DE PDF
# =========================================================
def generar_pdf_a4(datos, cantidad):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    ancho_et, alto_et = 95, 95 # Ajustado ligeramente el alto para ingredientes
    mx, my = 7, 10
    curr_x, curr_y = mx, my

    for i in range(cantidad):
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # Bloque 1: Cabecera (Nombre + Estado)
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(curr_x, curr_y, ancho_et, 18, 'F')
        pdf.set_xy(curr_x, curr_y + 2)
        pdf.set_font("Arial", 'B', 10)
        # Denominación Comercial + Estado según RD 1082/2025
        pdf.multi_cell(ancho_et, 4, str(datos['nombre_completo']).upper(), align='C')
        pdf.set_xy(curr_x, curr_y + 12)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C')

        # Bloque 2: Ingredientes y Alérgenos (Reglamento 1169)
        pdf.rect(curr_x, curr_y + 18, ancho_et, 15)
        pdf.set_xy(curr_x + 2, curr_y + 19)
        pdf.set_font("Arial", '', 7)
        ingredientes_texto = f"INGREDIENTES: {datos['ingredientes']}"
        pdf.multi_cell(ancho_et - 4, 3, ingredientes_texto)
        
        pdf.set_font("Arial", 'B', 7)
        pdf.set_x(curr_x + 2)
        # Alérgenos en Negrita/Mayúsculas
        pdf.multi_cell(ancho_et - 4, 3, f"CONTIENE: {str(datos['alergenos']).upper()}")
        pdf.set_font("Arial", 'I', 6)
        pdf.set_x(curr_x + 2)
        pdf.multi_cell(ancho_et - 4, 3, f"Puede contener: {datos['trazas']}")

        # Bloque 3: Origen
        pdf.rect(curr_x, curr_y + 33, ancho_et, 18)
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(curr_x + 5, curr_y + 35)
        if datos['zona']: pdf.cell(0, 4, f"- ZONA: {datos['zona']}")
        pdf.set_xy(curr_x + 5, curr_y + 39)
        pdf.cell(0, 4, f"- METODO: {datos['metodo']}")
        pdf.set_xy(curr_x + 5, curr_y + 43)
        if datos['arte']: pdf.cell(0, 4, f"- ARTE DE PESCA: {datos['arte']}")

        # Bloque 4: Conservación y Seguridad (RD 1082/2025)
        pdf.rect(curr_x, curr_y + 51, ancho_et, 10)
        pdf.set_xy(curr_x, curr_y + 52)
        pdf.set_font("Arial", 'B', 7)
        pdf.multi_cell(ancho_et, 3, datos['mencion_conservacion'], align='C')
        pdf.set_font("Arial", '', 6)
        pdf.cell(ancho_et, 3, "COCINAR COMPLETAMENTE ANTES DE CONSUMIR", align='C')

        # Bloque 5: Trazabilidad
        pdf.rect(curr_x, curr_y + 61, ancho_et, 18)
        pdf.set_xy(curr_x + 5, curr_y + 63)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 4, f"LOTE: {datos['lote']}")
        pdf.set_font("Arial", '', 8)
        if datos['f_descong']:
            pdf.set_xy(curr_x + 5, curr_y + 68)
            pdf.cell(0, 4, f"F. DESCONGELACION: {datos['f_descong']}")
        pdf.set_xy(curr_x + 5, curr_y + 72)
        pdf.cell(0, 4, f"F. CADUCIDAD: {datos['f_cad']}")

        # Bloque 6: Empresa y Óvalo
        pdf.rect(curr_x, curr_y + 79, ancho_et, 16)
        pdf.set_font("Arial", '', 6)
        pdf.set_xy(curr_x + 2, curr_y + 81)
        pdf.multi_cell(ancho_et - 30, 3, f"{datos['expedidor']}\nCalle Laguna del Marquesado 43C, Nave 43C\n28021 Madrid")
        
        pdf.ellipse(curr_x + 68, curr_y + 81, 22, 12)
        pdf.set_xy(curr_x + 68, curr_y + 83)
        pdf.set_font("Arial", 'B', 6)
        pdf.cell(22, 3, "ES", align='C', ln=True)
        pdf.set_xy(curr_x + 68, curr_y + 85)
        pdf.cell(22, 3, str(datos['ovalo']), align='C', ln=True)
        pdf.set_xy(curr_x + 68, curr_y + 87)
        pdf.cell(22, 3, "CE", align='C')

        if (i + 1) % 2 == 0:
            curr_x = mx
            curr_y += alto_et + 4
        else:
            curr_x += ancho_et + 4
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
st.title("Generador Etiquetas RD 1082/2025")

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

# Datos de Origen
zona = None
arte = None
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    st.subheader("📍 Datos de Origen")
    c3, c4 = st.columns(2)
    with c3: zona = st.selectbox("Zona FAO", preparar_lista(df_zonas, col_idx=0))
    with c4: arte = st.selectbox("Arte", preparar_lista(df_artes, col_idx=0))

fecha_descong = None
if "descongelado" in str(estado).lower():
    st.subheader("❄️ Datos de Descongelación")
    fecha_descong = st.date_input("Fecha de Descongelación", value=date.today())

# =========================================================
# PROCESAMIENTO Y LÓGICA DE NEGOCIO
# =========================================================
st.divider()

if st.button("🚀 GENERAR ETIQUETAS"):
    errores = []
    if "Selecciona una opción" in [nombre_base, forma, estado, metodo, expedidor]:
        errores.append("Faltan campos por elegir.")
    if not lote.strip():
        errores.append("El Lote es obligatorio.")

    if errores:
        for err in errores: st.warning(f"⚠️ {err}")
    else:
        # 1. Obtener datos base
        producto_data = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        genero = producto_data["GENERO"] if "GENERO" in producto_data else "M"
        
        # 2. Aplicar concordancia de género
        forma_adj = ajustar_genero(forma, genero)
        estado_adj = ajustar_genero(estado, genero)
        nombre_completo = f"{nombre_base} {forma_adj} {estado_adj}"
        
        # 3. Lógica de Conservación
        mencion_cons = "CONSERVAR ENTRE 0 Y 4ºC"
        if "descongelado" in estado.lower():
            mencion_cons = "PRODUCTO DESCONGELADO. NO VOLVER A CONGELAR. CONSERVAR A -18ºC"
        elif "congelado" in estado.lower():
            mencion_cons = "UNA VEZ DESCONGELADO NO VOLVER A CONGELAR. CONSERVAR A -18ºC"

        # 4. Lógica de Trazas (Desde Excel)
        trazas_reales = producto_data["TRAZAS"] if "TRAZAS" in producto_data else "Pescado"

        info_final = {
            "nombre_completo": nombre_completo,
            "nombre_cientifico": producto_data["NOMBRE_CIENTIFICO"],
            "ingredientes": producto_data["INGREDIENTES"] if "INGREDIENTES" in producto_data else "Pescado.",
            "alergenos": producto_data["ALERGENOS"],
            "trazas": trazas_reales,
            "metodo": metodo,
            "zona": zona if zona != "Selecciona una opción" else None,
            "arte": arte if arte != "Selecciona una opción" else None,
            "mencion_conservacion": mencion_cons,
            "lote": lote,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "f_descong": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "expedidor": expedidor, 
            "ovalo": df_exped[df_exped["EXPEDIDOR"] == expedidor]["OVALO_SANITARIO"].iloc[0]
        }

        pdf_res = generar_pdf_a4(info_final, cantidad)
        st.download_button("📥 DESCARGAR PDF", data=pdf_res, file_name=f"etiquetas_{lote}.pdf", mime="application/pdf")
