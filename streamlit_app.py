import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF

# =========================================================
# 1. CONFIGURACIÓN Y CARGA
# =========================================================
st.set_page_config(page_title="Generador Santiago y Santiago", layout="wide")

SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {
    "PRODUCTOS": "0", "FORMAS_TRANSFORMACION": "1141842769", "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476", "ZONAS_FAO": "907306114", "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266"
}

def limpiar_nan(texto):
    txt = str(texto)
    if txt.lower() == "nan" or not txt.strip() or txt == "0":
        return ""
    return txt

@st.cache_data(ttl=60)
def load_sheet(name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GIDS[name]}"
        return pd.read_csv(url)
    except: return pd.DataFrame()

df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")

def preparar_lista(df, col_name=None):
    if df is None or df.empty: return ["Selecciona una opción"]
    items = df[col_name].dropna().unique().tolist() if col_name else df.iloc[:, 0].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

# =========================================================
# 2. INTERFAZ
# =========================================================
st.title("🏷️ Generador de Etiquetas 10x16cm")

c1, c2 = st.columns(2)
with c1: nombre_base = st.selectbox("Producto", preparar_lista(df_productos, "NOMBRE_BASE"))
with c2: forma = st.selectbox("Transformación", preparar_lista(df_transform))

c3, c4, c5 = st.columns(3)
with c3: estado = st.selectbox("Estado", preparar_lista(df_estados))
with c4: metodo = st.selectbox("Producción", preparar_lista(df_metodo))
with c5: pais_orig = st.text_input("País de Origen", value="Marruecos")

lote = st.text_input("Número de Lote")

st.subheader("📅 Fechas")
fe1, fe2, fe3 = st.columns(3)
with fe1: f_elab = st.date_input("Fecha de Elaboración", value=date.today())
with fe2: 
    f_des = None
    if "DESCONGELADO" in str(estado).upper():
        f_des = st.date_input("Fecha de Descongelación", value=date.today())
with fe3: f_cad = st.date_input("Fecha de Caducidad", value=date.today() + timedelta(days=7))

# =========================================================
# 3. EL GENERADOR PDF "INTELIGENTE"
# =========================================================
def crear_pdf_final(d):
    pdf = FPDF(orientation='P', unit='mm', format=(100, 160))
    pdf.add_page()
    pdf.set_margins(8, 8, 8)
    
    # Marco
    pdf.rect(5, 5, 90, 150)

    # Cabecera
    pdf.set_font("Arial", 'B', 16)
    pdf.set_xy(8, 10)
    pdf.multi_cell(60, 7, d['nombre'].upper())
    
    pdf.set_x(8)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(60, 5, f"({d['cientifico']})", ln=True)
    
    pdf.set_x(8)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 5, d['forma'].lower(), ln=True)

    # LOTE
    pdf.rect(70, 10, 22, 18)
    pdf.set_xy(70, 11)
    pdf.set_font("Arial", '', 8)
    pdf.cell(22, 4, "LOTE:", align='C', ln=True)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_x(70)
    pdf.cell(22, 8, d['lote'], align='C')

    pdf.line(8, 32, 92, 32)
    
    # --- BLOQUE DINÁMICO DE INGREDIENTES ---
    y_actual = 35
    if d['ingredientes']:
        pdf.set_xy(8, y_actual)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(25, 5, "INGREDIENTES: ")
        pdf.set_font("Arial", '', 8)
        pdf.multi_cell(0, 4, d['ingredientes'])
        y_actual = pdf.get_y() + 2

    pdf.set_xy(8, y_actual)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(20, 5, "CONTIENE: ")
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, d['alergenos'], ln=True)
    
    y_actual = pdf.get_y() + 2
    pdf.line(8, y_actual, 92, y_actual)
    
    # Trazabilidad
    y_actual += 3
    pdf.set_font("Arial", 'B', 9)
    infos = [("ZONA DE CAPTURA:", d['zona']), ("ARTE DE PESCA:", d['arte']), 
             ("MÉTODO DE PESCA:", d['metodo']), ("PAÍS DE ORIGEN:", d['pais'])]
    
    for label, val in infos:
        if val and val != "N/A":
            pdf.set_xy(8, y_actual)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(pdf.get_string_width(label)+2, 5, label)
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 5, str(val), ln=True)
            y_actual += 5

    # Conservación (Posición fija abajo)
    pdf.line(8, 95, 92, 95)
    pdf.set_xy(8, 98)
    pdf.set_font("Arial", 'B', 9)
    mencion = "CONSERVAR ENTRE 0-4ºC. COCINAR ANTES DE CONSUMIR."
    if "CONGELADO" in d['estado'].upper():
        mencion = "CONSERVAR A -18ºC. UNA VEZ DESCONGELADO NO VOLVER A CONGELAR."
    elif "DESCONGELADO" in d['estado'].upper():
        mencion = "CONSERVAR ENTRE 0-4ºC. NO VOLVER A CONGELAR."
    pdf.multi_cell(84, 5, mencion, align='C')

    # Fechas
    pdf.line(8, 115, 92, 115)
    pdf.set_xy(8, 118)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(84, 5, f"F. ELABORACIÓN: {d['f_el']}", align='C', ln=True)
    if d['f_des']:
        pdf.cell(84, 5, f"F. DESCONGELACIÓN: {d['f_des']}", align='C', ln=True)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(84, 10, f"F. CAD: {d['f_cad']}", align='C', ln=True)

    # Pie
    pdf.line(8, 140, 92, 140)
    pdf.set_xy(8, 142)
    pdf.set_font("Arial", '', 7)
    pdf.multi_cell(60, 3, "PESCADOS Y MARISCOS SANTIAGO Y SANTIAGO S.L.\nCalle Laguna del Marquesado 43C, 28021, Madrid")
    pdf.ellipse(72, 142, 18, 10)
    pdf.set_xy(72, 143.5)
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(18, 3, "ES", align='C', ln=True)
    pdf.set_x(72)
    pdf.cell(18, 3, "12.14276/M", align='C')

    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# =========================================================
# 4. BOTÓN
# =========================================================
if nombre_base != "Selecciona una opción" and lote:
    row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
    
    # Carga dinámica: Zonas y Artes solo si no es acuicultura
    z_f = "N/A"
    a_f = "N/A"
    if "acuicultura" not in str(metodo).lower():
        # Aquí deberías tener los selectboxes de zona y arte como antes
        z_f = "FAO 27" # Ejemplo, conéctalo con tu selectbox
        a_f = "Arrastre" # Ejemplo

    pdf_data = crear_pdf_final({
        "nombre": nombre_base, "cientifico": row["NOMBRE_CIENTIFICO"],
        "forma": forma, "estado": estado, "lote": lote,
        "ingredientes": limpiar_nan(row["INGREDIENTES"]),
        "alergenos": limpiar_nan(row["ALERGENOS"]),
        "metodo": metodo, "zona": z_f, "arte": a_f, "pais": pais_orig,
        "f_el": f_elab.strftime("%d/%m/%Y"),
        "f_des": f_des.strftime("%d/%m/%Y") if f_des else None,
        "f_cad": f_cad.strftime("%d/%m/%Y")
    })

    st.download_button("📥 DESCARGAR PDF 10x16", pdf_data, f"{lote}.pdf", "application/pdf")














