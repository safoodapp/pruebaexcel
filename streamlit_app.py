import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF

# =========================================================
# 1. CONFIGURACIÓN Y ESTILO (ACCESIBILIDAD +50 AÑOS)
# =========================================================
st.set_page_config(page_title="Generador de Etiquetas de Santiago y Santiago", layout="wide")

# CSS para agrandar textos, botones e inputs
st.markdown("""
    <style>
    html, body, [class*="st-at"] { font-size: 1.2rem; }
    .stButton>button { height: 3em; width: 100%; font-size: 1.5rem !important; font-weight: bold; }
    .stSelectbox label, .stTextInput label, .stDateInput label, .stNumberInput label {
        font-size: 1.3rem !important; font-weight: bold !important; color: #1E3A8A;
    }
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def limpiar_nan(texto):
    txt = str(texto)
    return "" if txt.lower() == "nan" or not txt.strip() else txt

# =========================================================
# 2. CARGA DE DATOS (GOOGLE SHEETS)
# =========================================================
SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {
    "PRODUCTOS": "0", "FORMAS_TRANSFORMACION": "1141842769", "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476", "ZONAS_FAO": "907306114", "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266", "TRAZAS_CONFIG": "1059656739",
}

@st.cache_data(ttl=600)
def load_sheet(name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GIDS[name]}"
    return pd.read_csv(url)

def preparar_lista(df, col_idx=None, col_name=None):
    if col_name: items = df[col_name].dropna().unique().tolist()
    else: items = df.iloc[:, col_idx].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_exped = load_sheet("EXPEDIDORES")
df_trazas_config = load_sheet("TRAZAS_CONFIG")

# =========================================================
# 3. LÓGICA DE INTERFAZ
# =========================================================
st.title("🏷️ Generador de Etiquetas de Santiago y Santiago")

# Botón Nueva Etiqueta (Reset)
if st.sidebar.button("🔄 NUEVA ETIQUETA / LIMPIAR"):
    st.rerun()

col1, col2 = st.columns([1, 1])

with col1:
    nombre_base = st.selectbox("Producto", preparar_lista(df_productos, col_name="NOMBRE_BASE"))
    forma = st.selectbox("Transformación", preparar_lista(df_transform, col_idx=0))
    estado = st.selectbox("Estado", preparar_lista(df_estados, col_idx=0))
    lote = st.text_input("Número de Lote")

with col2:
    metodo = st.selectbox("Producción", preparar_lista(df_metodo, col_idx=0))
    
    # Lógica de Fechas Reordenada y Automática
    f_descong_val = date.today()
    f_cad_val = date.today()
    
    # Mostrar Descongelación antes que Caducidad si aplica
    if "DESCONGELADO" in str(estado).upper():
        f_descong_val = st.date_input("Fecha de Descongelación", value=date.today())
        # Automático +3 días
        f_cad_val = f_descong_val + timedelta(days=3)
        fecha_cad = st.date_input("Fecha de Caducidad (Auto +3 días)", value=f_cad_val)
    else:
        fecha_cad = st.date_input("Fecha de Caducidad")
        f_descong_val = None

    cantidad = st.number_input("Número de etiquetas a imprimir", min_value=1, value=1)
    expedidor_auto = df_exped.iloc[0]["EXPEDIDOR"]
    ovalo_auto = df_exped.iloc[0]["OVALO_SANITARIO"]

# Mantener visibilidad condicional original
zona, arte = None, None
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    c3, c4 = st.columns(2)
    with c3: zona = st.selectbox("Zona FAO", preparar_lista(df_zonas, col_idx=0))
    with c4: arte = st.selectbox("Arte", preparar_lista(df_artes, col_idx=0))

# =========================================================
# 4. FUNCIÓN DE DIBUJO PDF (ETIQUETA COMPACTA)
# =========================================================
def generar_pdf_a4(datos, cantidad):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    ancho_et, alto_et = 95, 95
    mx, my, sep = 7, 10, 5 
    curr_x, curr_y = mx, my

    for i in range(int(cantidad)):
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # PRODUCTO Y NOMBRE CIENTÍFICO (DEBAJO)
        pdf.set_xy(curr_x, curr_y + 4)
        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(ancho_et, 5, f"{datos['nombre_base'].upper()}\nPRODUCTO {datos['mencion_estado'].upper()}", align='C')
        
        pdf.set_font("Arial", 'I', 9)
        pdf.set_xy(curr_x, curr_y + 15)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C')

        # INGREDIENTES CON AJUSTE DE TAMAÑO (NO CRECE)
        pdf.line(curr_x, curr_y + 20, curr_x + ancho_et, curr_y + 20)
        if datos['ingredientes']:
            # Si el texto es muy largo, bajamos la fuente de 7 a 6
            tam_font_ing = 7 if len(datos['ingredientes']) < 150 else 6
            pdf.set_xy(curr_x + 2, curr_y + 21)
            pdf.set_font("Arial", 'B', tam_font_ing)
            pdf.write(3, "INGREDIENTES: ")
            pdf.set_font("Arial", '', tam_font_ing)
            pdf.write(3, datos['ingredientes'])
        
        # ALÉRGENOS (Posición fija para que no se pisen)
        pdf.set_xy(curr_x + 2, curr_y + 34)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(ancho_et, 4, f"CONTIENE: {str(datos['alergenos']).upper()}")
        
        if datos['trazas']:
            pdf.set_xy(curr_x + 2, curr_y + 38)
            pdf.set_font("Arial", 'I', 7.5)
            pdf.cell(ancho_et, 4, f"Puede contener: {datos['trazas']}")

        # ORIGEN Y MÉTODO (NEGRITAS Y TEXTO CORREGIDO)
        pdf.rect(curr_x, curr_y + 43, ancho_et, 16)
        pdf.set_font("Arial", 'B', 8)
        pdf.set_xy(curr_x + 3, curr_y + 44)
        pdf.write(4, "ZONA DE CAPTURA: ")
        pdf.set_font("Arial", '', 8)
        pdf.write(4, f"{datos['zona'] if datos['zona'] else 'N/A'}")
        
        pdf.set_xy(curr_x + 3, curr_y + 49)
        pdf.set_font("Arial", 'B', 8)
        pdf.write(4, "MÉTODO DE PESCA: ")
        pdf.set_font("Arial", '', 8)
        pdf.write(4, f"{datos['metodo']}")
        
        pdf.set_xy(curr_x + 3, curr_y + 54)
        pdf.set_font("Arial", 'B', 8)
        pdf.write(4, "ARTE DE PESCA: ")
        pdf.set_font("Arial", '', 8)
        pdf.write(4, f"{datos['arte'] if datos['arte'] else 'N/A'}")

        # CONSERVACIÓN
        pdf.rect(curr_x, curr_y + 60, ancho_et, 8)
        pdf.set_xy(curr_x + 2, curr_y + 61)
        pdf.set_font("Arial", 'B', 7)
        pdf.multi_cell(ancho_et - 4, 3, datos['mencion_conservacion'].upper(), align='C')

        # TRAZABILIDAD (LOTE Y FECHAS GRANDES)
        pdf.rect(curr_x, curr_y + 69, ancho_et, 13)
        pdf.set_xy(curr_x + 3, curr_y + 70)
        pdf.set_font("Arial", 'B', 12) # Lote más grande
        pdf.cell(0, 5, f"LOTE: {datos['lote']}")
        
        pdf.set_font("Arial", 'B', 10) # Fechas más grandes
        pdf.set_xy(curr_x + 3, curr_y + 76)
        f_desc_txt = f"  DESCONG: {datos['f_descong']}" if datos['f_descong'] else ""
        pdf.cell(0, 5, f"CAD: {datos['f_cad']}{f_desc_txt}")

        # EMPRESA Y ÓVALO
        pdf.set_xy(curr_x + 2, curr_y + 83)
        pdf.set_font("Arial", '', 7)
        pdf.multi_cell(ancho_et - 25, 3, f"{datos['expedidor']}\n28021 Madrid")
        
        pdf.ellipse(curr_x + 72, curr_y + 83, 18, 10)
        pdf.set_xy(curr_x + 72, curr_y + 84)
        pdf.set_font("Arial", 'B', 6)
        pdf.cell(18, 2.5, "ES", align='C', ln=True)
        pdf.set_x(curr_x + 72)
        pdf.cell(18, 2.5, str(datos['ovalo']), align='C', ln=True)
        pdf.set_x(curr_x + 72)
        pdf.cell(18, 2.5, "CE", align='C')

        # Salto de etiqueta
        if (i + 1) % 2 == 0:
            curr_x = mx
            curr_y += alto_et + sep
        else:
            curr_x += ancho_et + sep
        if (i + 1) % 6 == 0 and (i + 1) < cantidad:
            pdf.add_page()
            curr_x, curr_y = mx, my
            
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 5. BOTÓN GENERAR
# =========================================================
if st.button("🚀 GENERAR ETIQUETAS"):
    if nombre_base == "Selecciona una opción" or not lote:
        st.error("⚠️ Por favor, selecciona un Producto e introduce un Lote.")
    else:
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        
        # Mención de conservación
        mencion_cons = "CONSERVAR ENTRE 0 Y 4ºC"
        if "DESCONGELADO" in estado.upper():
            mencion_cons = "PRODUCTO DESCONGELADO. NO VOLVER A CONGELAR. CONSERVAR A -18ºC"
        elif "CONGELADO" in estado.upper():
            mencion_cons = "UNA VEZ DESCONGELADO NO VOLVER A CONGELAR. CONSERVAR A -18ºC"

        # Trazas
        alergeno_p = limpiar_nan(prod_row["ALERGENOS"])
        trazas_f = ""
        if alergeno_p:
            mask = df_trazas_config["ALERGENO"].astype(str).str.strip().str.upper() == alergeno_p.strip().upper()
            match = df_trazas_config[mask]
            if not match.empty:
                trazas_f = limpiar_nan(match["PUEDE_CONTENER"].iloc[0])

        info_etiqueta = {
            "nombre_base": f"{nombre_base} {forma if forma != 'Selecciona una opción' else ''}",
            "mencion_estado": estado,
            "nombre_cientifico": prod_row["NOMBRE_CIENTIFICO"],
            "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
            "alergenos": alergeno_p,
            "trazas": trazas_f,
            "mencion_conservacion": mencion_cons,
            "metodo": metodo, 
            "lote": lote,
            "zona": zona,
            "arte": arte,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "f_descong": f_descong_val.strftime("%d/%m/%Y") if f_descong_val else None,
            "expedidor": expedidor_auto,
            "ovalo": ovalo_auto
        }

        with st.spinner('Generando PDF...'):
            pdf_bytes = generar_pdf_a4(info_etiqueta, cantidad)
            st.success("✅ ¡Etiquetas listas!")
            st.download_button("📥 DESCARGAR PDF PARA IMPRIMIR", data=pdf_bytes, file_name=f"etiquetas_{lote}.pdf", mime="application/pdf")



