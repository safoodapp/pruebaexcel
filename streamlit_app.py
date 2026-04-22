import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF

# =========================================================
# 1. CONFIGURACIÓN Y CARGA DE DATOS
# =========================================================
st.set_page_config(page_title="Generador de etiquetas Santiago y Santiago", layout="wide")

SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {
    "PRODUCTOS": "0", 
    "FORMAS_TRANSFORMACION": "1141842769", 
    "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476", 
    "ZONAS_FAO": "907306114", 
    "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266",
    "PAIS_ORIGEN": "TU_GID_AQUI" 
}

def limpiar_nan(texto):
    txt = str(texto)
    return "" if txt.lower() == "nan" or not txt.strip() or txt == "0" else txt

@st.cache_data(ttl=60)
def load_sheet(name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GIDS[name]}"
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

df_productos = load_sheet("PRODUCTOS")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_paises = load_sheet("PAIS_ORIGEN")

def preparar_lista(df, col_name=None):
    if df is None or df.empty: return ["Selecciona una opción"]
    items = df[col_name].dropna().unique().tolist() if col_name else df.iloc[:, 0].dropna().unique().tolist()
    return ["Selecciona una opción"] + sorted(items)

# =========================================================
# 2. INTERFAZ DE USUARIO
# =========================================================
st.title("🏷️ Generador de Etiquetas Santiago y Santiago")

c1, c2 = st.columns(2)
with c1: nombre_base = st.selectbox("Producto", preparar_lista(df_productos, "NOMBRE_BASE"))
with c2: lote = st.text_input("🔢 Número de Lote")

c3, c4, c5 = st.columns(3)
with c3: estado = st.selectbox("Estado", preparar_lista(df_estados))
with c4: metodo = st.selectbox("Producción", preparar_lista(df_metodo))
with c5: pais_orig = st.selectbox("País de Origen", preparar_lista(df_paises))

zona_sel, arte_sel = "N/A", "N/A"
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    c6, c7 = st.columns(2)
    with c6: zona_sel = st.selectbox("Zona FAO", preparar_lista(df_zonas))
    with c7: arte_sel = st.selectbox("Arte de Pesca", preparar_lista(df_artes))

st.subheader("📅 Fechas")
fe1, fe2, fe3 = st.columns(3)
with fe1: f_elab = st.date_input("Fecha de Elaboración", value=date.today())
with fe2:
    f_des_val = None
    if "DESCONGELADO" in str(estado).upper():
        f_des_val = st.date_input("Fecha de Descongelación", value=date.today())
with fe3:
    f_cad_val = st.date_input("Fecha de Caducidad", value=date.today() + timedelta(days=7))

# =========================================================
# 3. LÓGICA DEL PDF (AJUSTADO A PLANTILLA ORIGINAL)
# =========================================================
def generar_pdf(d):
    pdf = FPDF(orientation='P', unit='mm', format=(100, 160))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.rect(5, 5, 90, 150)

    # CABECERA (Sin transformación como pediste)
    pdf.set_font("Arial", 'B', 16)
    pdf.set_xy(8, 12)
    pdf.multi_cell(60, 7, d['nombre'].upper())
    
    pdf.set_font("Arial", 'I', 10); pdf.set_x(8)
    pdf.cell(60, 5, f"({d['cientifico']})", ln=True)

    # LOTE
    pdf.rect(70, 10, 22, 17)
    pdf.set_xy(70, 11); pdf.set_font("Arial", '', 8); pdf.cell(22, 4, "LOTE:", align='C', ln=True)
    pdf.set_font("Arial", 'B', 13); pdf.set_x(70); pdf.cell(22, 7, d['lote'], align='C')

    pdf.line(8, 33, 92, 33)
    
    # CUERPO DINÁMICO (Ajustado a "Puede contener trazas de")
    y_dyn = 36
    if d['ingredientes']:
        pdf.set_xy(8, y_dyn)
        pdf.set_font("Arial", 'B', 9); pdf.cell(25, 4, "INGREDIENTES: ")
        pdf.set_font("Arial", '', 7.5); pdf.multi_cell(60, 3.5, d['ingredientes'])
        y_dyn = pdf.get_y() + 2

    if d['alergenos']:
        pdf.set_xy(8, y_dyn)
        pdf.set_font("Arial", 'I', 8); pdf.cell(0, 5, f"Puede contener trazas de: {d['alergenos']}", ln=True)
        y_dyn = pdf.get_y() + 1
    
    pdf.line(8, y_dyn + 1, 92, y_dyn + 1)
    y_dyn += 4

    # TRAZABILIDAD
    pdf.set_font("Arial", 'B', 9)
    for lab, val in [("ORIGEN:", d['pais']), ("ZONA DE CAPTURA:", d['zona']), 
                     ("ARTE DE PESCA:", d['arte']), ("MÉTODO DE PESCA:", d['metodo'])]:
        if val and val != "N/A" and val != "Selecciona una opción":
            pdf.set_xy(8, y_dyn); pdf.set_font("Arial", 'B', 9)
            pdf.cell(pdf.get_string_width(lab)+2, 4, lab)
            pdf.set_font("Arial", '', 9); pdf.cell(0, 4, str(val), ln=True)
            y_dyn += 4.5

    # --- BLOQUES ANCLADOS ---
    # Conservación corregida para DESCONGELADO
    pdf.line(8, 92, 92, 92)
    pdf.set_xy(8, 95); pdf.set_font("Arial", 'B', 9)
    pdf.multi_cell(84, 4.5, d['mencion'], align='C')
    pdf.set_font("Arial", '', 9); pdf.cell(84, 5, f"producto {d['estado'].lower()}", align='C', ln=True)

    # Fechas
    pdf.line(8, 114, 92, 114)
    pdf.set_xy(8, 118); pdf.set_font("Arial", 'B', 10)
    pdf.cell(84, 5, f"F. ELABORACIÓN: {d['f_el']}", align='C', ln=True)
    if d['f_des']:
        pdf.cell(84, 5, f"F. DESCONGELACIÓN: {d['f_des']}", align='C', ln=True)
    pdf.set_font("Arial", 'B', 15); pdf.set_xy(8, 130); pdf.cell(84, 10, f"F. CADUCIDAD: {d['f_cad']}", align='C', ln=True)

    # Pie y Óvalo
    pdf.line(8, 142, 92, 142)
    pdf.set_xy(8, 144); pdf.set_font("Arial", '', 7.5)
    pdf.multi_cell(55, 3.5, "PESCADOS Y MARISCOS SANTIAGO Y SANTIAGO S.L.\nCalle Laguna del Marquesado 43C, 28021, Madrid")
    pdf.ellipse(72, 144, 18, 9); pdf.set_xy(72, 145.5); pdf.set_font("Arial", 'B', 7)
    pdf.cell(18, 3, "ES", align='C', ln=True); pdf.set_x(72); pdf.cell(18, 3, "12.14276/M", align='C')

    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# =========================================================
# 4. EJECUCIÓN
# =========================================================
if nombre_base != "Selecciona una opción" and lote:
    row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
    
    # Lógica de mención corregida (0-4ºC para descongelado)
    mencion = "CONSERVAR ENTRE 0-4ºC. COCINAR ANTES DE CONSUMIR."
    if "CONGELADO" in estado.upper(): 
        mencion = "CONSERVAR A -18ºC. UNA VEZ DESCONGELADO NO VOLVER A CONGELAR."
    elif "DESCONGELADO" in estado.upper(): 
        mencion = "CONSERVAR ENTRE 0 Y 4ºC. NO VOLVER A CONGELAR."

    pdf_data = generar_pdf({
        "nombre": nombre_base, "cientifico": row["NOMBRE_CIENTIFICO"],
        "estado": estado, "lote": lote,
        "ingredientes": limpiar_nan(row["INGREDIENTES"]),
        "alergenos": limpiar_nan(row["ALERGENOS"]),
        "metodo": metodo, "zona": zona_sel, "arte": arte_sel, "pais": pais_orig,
        "f_el": f_elab.strftime("%d/%m/%Y"),
        "f_des": f_des_val.strftime("%d/%m/%Y") if f_des_val else None,
        "f_cad": f_cad_val.strftime("%d/%m/%Y"),
        "mencion": mencion
    })

    st.download_button(label="📥 DESCARGAR ETIQUETA", data=pdf_data, file_name=f"Etiqueta_{lote}.pdf", mime="application/pdf", use_container_width=True)
