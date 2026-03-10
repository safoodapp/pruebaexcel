import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF

# =========================================================
# 1. CONFIGURACIÓN Y CARGA DE DATOS
# =========================================================
st.set_page_config(page_title="Generador Santiago y Santiago", layout="wide")

SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {
    "PRODUCTOS": "0", "FORMAS_TRANSFORMACION": "1141842769", "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476", "ZONAS_FAO": "907306114", "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266", "TRAZAS_CONFIG": "1059656739",
    "PAIS_ORIGEN": "TU_GID_AQUI" # Reemplaza con el GID real cuando lo tengas
}

def limpiar_nan(texto):
    txt = str(texto)
    return "" if txt.lower() == "nan" or not txt.strip() else txt

@st.cache_data(ttl=60)
def load_sheet(name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GIDS[name]}"
        return pd.read_csv(url)
    except:
        if name == "PAIS_ORIGEN":
            return pd.DataFrame({"PAIS": ["España", "Marruecos", "Portugal", "Islandia", "Noruega"]})
        return pd.DataFrame()

df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_exped = load_sheet("EXPEDIDORES")
df_trazas_config = load_sheet("TRAZAS_CONFIG")
df_paises = load_sheet("PAIS_ORIGEN")

def preparar_lista(df, col_name=None):
    if df.empty: return ["Selecciona una opción"]
    items = df[col_name].dropna().unique().tolist() if col_name else df.iloc[:, 0].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

# =========================================================
# 2. INTERFAZ DE USUARIO
# =========================================================
st.title("🏷️ Generador de Etiquetas Profesional")

c1, c2 = st.columns(2)
with c1: nombre_base = st.selectbox("Producto", preparar_lista(df_productos, "NOMBRE_BASE"))
with c2: forma = st.selectbox("Transformación", preparar_lista(df_transform))

c3, c4, c5 = st.columns(3)
with c3: estado = st.selectbox("Estado", preparar_lista(df_estados))
with c4: metodo = st.selectbox("Producción", preparar_lista(df_metodo))
with c5: pais_orig = st.selectbox("País de Origen", preparar_lista(df_paises))

zona, arte = "N/A", "N/A"
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    c6, c7 = st.columns(2)
    with c6: zona = st.selectbox("Zona FAO", preparar_lista(df_zonas))
    with c7: arte = st.selectbox("Arte de Pesca", preparar_lista(df_artes))

lote = st.text_input("Número de Lote")

# --- LÓGICA DE FECHAS CORREGIDA ---
c8, c9 = st.columns(2)
fecha_descong = None
with c8:
    if "DESCONGELADO" in str(estado).upper():
        fecha_descong = st.date_input("Fecha de Descongelación", value=date.today())

with c9:
    default_cad = date.today() + timedelta(days=3) if fecha_descong else date.today()
    fecha_cad = st.date_input("Fecha de Caducidad", value=default_cad)

cantidad = st.number_input("Número de etiquetas", min_value=1, value=1)

# =========================================================
# 3. FUNCIÓN DEL PDF (DISEÑO DINÁMICO)
# =========================================================
def generar_pdf_final(datos, cantidad):
    pdf = FPDF(orientation='P', unit='mm', format=(100, 150))
    pdf.set_auto_page_break(auto=False)
    
    for _ in range(int(cantidad)):
        pdf.add_page()
        mx = 8
        ancho_util = 100 - (mx * 2)

        # CABECERA: Producto (Izquierda) y Lote (Derecha)
        pdf.set_xy(mx, 10)
        pdf.set_font("Arial", 'B', 15)
        txt_prod = f"{datos['nombre_base']} {datos['forma']}".strip()
        pdf.multi_cell(55, 7, txt_prod.upper(), align='L')
        
        pdf.set_x(mx)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(55, 5, f"({datos['nombre_cientifico']})", ln=True)
        
        pdf.set_x(mx)
        pdf.set_font("Arial", '', 11)
        pdf.cell(55, 5, f"producto {datos['mencion_estado'].lower()}", ln=True)

        # Cuadro LOTE
        pdf.rect(65, 10, 28, 20)
        pdf.set_xy(65, 12)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(28, 5, "LOTE:", align='C', ln=True)
        pdf.set_x(65)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(28, 8, datos['lote'], align='C')
        
        y_pos = 35
        pdf.line(mx, y_pos, 100-mx, y_pos)
        y_pos += 5

        # INGREDIENTES Y ALÉRGENOS (DINÁMICO)
        if datos['ingredientes']:
            pdf.set_xy(mx, y_pos)
            pdf.set_font("Arial", 'B', 9)
            pdf.write(5, "INGREDIENTES: ")
            pdf.set_font("Arial", '', 9)
            pdf.multi_cell(ancho_util - 25, 5, datos['ingredientes'], align='J')
            y_pos = pdf.get_y() + 3

        pdf.set_xy(mx, y_pos)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(ancho_util, 6, f"CONTIENE: {str(datos['alergenos']).upper()}", ln=True)
        
        if datos['trazas']:
            pdf.set_x(mx)
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(ancho_util, 5, f"Puede contener trazas de: {datos['trazas']}", ln=True)
        
        y_pos = pdf.get_y() + 4
        pdf.line(mx, y_pos, 100-mx, y_pos)
        y_pos += 5

        # TRAZABILIDAD
        pdf.set_xy(mx, y_pos)
        pdf.set_font("Arial", 'B', 10)
        if "acuicultura" not in str(datos['metodo']).lower():
            pdf.cell(ancho_util, 6, f"ZONA DE CAPTURA: {datos['zona']}", ln=True, align='C')
            pdf.set_x(mx)
            pdf.cell(ancho_util, 6, f"ARTE DE PESCA: {datos['arte']}", ln=True, align='C')
        
        pdf.set_x(mx)
        pdf.cell(ancho_util, 6, f"MÉTODO DE PESCA: {datos['metodo']}", ln=True, align='C')
        pdf.set_x(mx)
        pdf.cell(ancho_util, 6, f"PAÍS DE ORIGEN: {datos['pais']}", ln=True, align='C')

        # CONSERVACIÓN
        pdf.line(mx, 100, 100-mx, 100)
        pdf.set_xy(mx, 103)
        pdf.set_font("Arial", 'B', 9)
        pdf.multi_cell(ancho_util, 4.5, datos['mencion_conservacion'], align='C')

        # FECHAS
        pdf.line(mx, 122, 100-mx, 122)
        pdf.set_xy(mx, 125)
        if datos['f_des']:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(ancho_util, 6, f"F. DESCONGELACIÓN: {datos['f_des']}", align='C', ln=True)
            pdf.set_x(mx)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(ancho_util, 8, f"F. CAD: {datos['f_cad']}", align='C')

        # PIE
        pdf.line(mx, 140, 100-mx, 140)
        pdf.set_xy(mx, 142)
        pdf.set_font("Arial", '', 7)
        info_exp = df_exped.iloc[0]["EXPEDIDOR"] if not df_exped.empty else "PESCADOS SANTIAGO S.L."
        pdf.multi_cell(ancho_util - 30, 3, info_exp)
        
        pdf.ellipse(72, 141, 22, 8)
        pdf.set_xy(72, 142)
        pdf.set_font("Arial", 'B', 6)
        pdf.cell(22, 2, "ES", align='C', ln=True)
        pdf.set_x(72)
        ov = df_exped.iloc[0]["OVALO_SANITARIO"] if not df_exped.empty else "12.345/M"
        pdf.cell(22, 2, ov, align='C')

    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# =========================================================
# 4. PROCESAMIENTO Y BOTÓN
# =========================================================
if st.button("🚀 GENERAR ETIQUETAS"):
    if nombre_base == "Selecciona una opción" or not lote:
        st.error("⚠️ Falta Producto o Lote")
    else:
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        
        # Trazas
        alergeno_p = limpiar_nan(prod_row["ALERGENOS"])
        trazas_f = ""
        if alergeno_p and not df_trazas_config.empty:
            mask = df_trazas_config["ALERGENO"].astype(str).str.upper() == alergeno_p.upper()
            match = df_trazas_config[mask]
            if not match.empty: trazas_f = limpiar_nan(match["PUEDE_CONTENER"].iloc[0])

        # Conservación
        mencion_cons = "CONSERVAR ENTRE 0-4ºC. COCINAR ANTES DE CONSUMIR."
        if "CONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR A -18ºC. NO VOLVER A CONGELAR."
        elif "DESCONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. NO VOLVER A CONGELAR."

        pdf_bytes = generar_pdf_final({
            "nombre_base": nombre_base,
            "forma": forma if forma != "Selecciona una opción" else "",
            "nombre_cientifico": prod_row["NOMBRE_CIENTIFICO"],
            "mencion_estado": estado,
            "lote": lote,
            "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
            "alergenos": alergeno_p,
            "trazas": trazas_f,
            "metodo": metodo, "zona": zona, "arte": arte, "pais": pais_orig,
            "mencion_conservacion": mencion_cons,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "f_des": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "ovalo": df_exped.iloc[0]["OVALO_SANITARIO"] if not df_exped.empty else "12.345/M"
        }, cantidad)

        st.success("✅ Etiquetas listas")
        st.download_button("📥 DESCARGAR PDF", pdf_bytes, f"etiquetas_{lote}.pdf", "application/pdf")












































