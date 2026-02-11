import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF

# =========================================================
# 1. CONFIGURACIÓN Y ESTILO
# =========================================================
st.set_page_config(page_title="Generador de Etiquetas de Santiago y Santiago", layout="wide")

st.markdown("""
    <style>
    .stSelectbox label, .stTextInput label, .stDateInput label, .stNumberInput label {
        font-size: 1.4rem !important; font-weight: bold !important; color: #1E3A8A !important;
    }
    .stButton>button { height: 3em; font-size: 1.3rem !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

def limpiar_nan(texto):
    txt = str(texto)
    return "" if txt.lower() == "nan" or not txt.strip() else txt

# =========================================================
# 2. CARGA DE DATOS
# =========================================================
SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {
    "PRODUCTOS": "0", "FORMAS_TRANSFORMACION": "1141842769", "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476", "ZONAS_FAO": "907306114", "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266", "TRAZAS_CONFIG": "1059656739"
}

@st.cache_data(ttl=60)
def load_sheet(name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GIDS[name]}"
    return pd.read_csv(url)

# Cargar dataframes
df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_exped = load_sheet("EXPEDIDORES")
df_trazas_config = load_sheet("TRAZAS_CONFIG")

def preparar_lista(df, col_idx=None, col_name=None):
    if col_name: items = df[col_name].dropna().unique().tolist()
    else: items = df.iloc[:, col_idx].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

# =========================================================
# 3. INTERFAZ
# =========================================================
st.title("🏷️ Generador de Etiquetas de Santiago y Santiago")

if st.sidebar.button("🔄 NUEVA ETIQUETA / LIMPIAR"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

c1, c2 = st.columns(2)
with c1: nombre_base = st.selectbox("Producto", preparar_lista(df_productos, col_name="NOMBRE_BASE"), key="p1")
with c2: forma = st.selectbox("Transformación", preparar_lista(df_transform, col_idx=0), key="p2")

c3, c4 = st.columns(2)
with c3: estado = st.selectbox("Estado", preparar_lista(df_estados, col_idx=0), key="p3")
with c4: metodo = st.selectbox("Producción", preparar_lista(df_metodo, col_idx=0), key="p4")

zona, arte = "N/A", "N/A"
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    c5, c6 = st.columns(2)
    with c5: zona = st.selectbox("Zona FAO", preparar_lista(df_zonas, col_idx=0), key="p5")
    with c6: arte = st.selectbox("Arte de Pesca", preparar_lista(df_artes, col_idx=0), key="p6")

lote = st.text_input("Número de Lote", key="p7")

c7, c8 = st.columns(2)
fecha_descong = None
with c7:
    if "DESCONGELADO" in str(estado).upper():
        fecha_descong = st.date_input("Fecha de Descongelación", value=date.today(), key="p8")
with c8:
    def_cad = date.today()
    if "DESCONGELADO" in str(estado).upper() and fecha_descong:
        def_cad = fecha_descong + timedelta(days=3)
    fecha_cad = st.date_input("Fecha de Caducidad", value=def_cad, key="p9")

cantidad = st.number_input("Número de etiquetas", min_value=1, value=1, key="p10")

# =========================================================
# 4. FUNCIÓN PDF CORREGIDA
# =========================================================

def generar_pdf_a4(datos, cantidad):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    
    ancho_et, alto_et = 102, 76
    mx, my, sep = 5, 10, 5 
    curr_x, curr_y = mx, my
    ancho_util = ancho_et - 8 # Margen de seguridad lateral

    for i in range(int(cantidad)):
        # 0. RECUADRO EXTERIOR
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # 1. CABECERA
        pdf.set_xy(curr_x, curr_y + 4)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(ancho_et, 4.5, datos['nombre_base'].upper(), align='C')
        
        pdf.set_font("Arial", 'I', 8.5)
        pdf.set_x(curr_x)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C', ln=True)
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(ancho_et, 5, f"PRODUCTO {datos['mencion_estado'].upper()}", align='C', ln=True)


        # 2. INGREDIENTES Y ALÉRGENOS
        pdf.set_xy(curr_x + 4, y_linea1 + 1.5)

        if datos['ingredientes'] and str(datos['ingredientes']).strip():
        # Solo el título en negrita
        pdf.set_font("Arial", 'B', 7.5)
        pdf.cell(22, 3.5, "INGREDIENTES:", ln=0)

        # Texto normal en la misma línea
        pdf.set_font("Arial", '', 7.5)
        pdf.multi_cell(ancho_util - 22, 3.5, f" {datos['ingredientes']}", align='L')
        else:
        pdf.set_y(pdf.get_y() + 2)
        
        # Alérgenos (siempre debajo de ingredientes)
        pdf.set_x(curr_x + 4)
        pdf.set_font("Arial", 'B', 8.5)
        pdf.cell(ancho_util, 4.5, f"CONTIENE: {str(datos['alergenos']).upper()}", ln=True)
        
        if datos['trazas']:
            pdf.set_x(curr_x + 4)
            pdf.set_font("Arial", 'I', 7.5)
            pdf.cell(ancho_util, 3.5, f"Puede contener trazas de: {datos['trazas']}", ln=True)

        # 3. DATOS DE PESCA (Anclado a posición media)
        y_linea2 = curr_y + 45
        pdf.line(curr_x, y_linea2, curr_x + ancho_et, y_linea2)
        pdf.set_xy(curr_x, y_linea2 + 1)
        pdf.set_font("Arial", 'B', 7.5)
        texto_pesca = f"ZONA: {datos['zona']}  |  MÉTODO: {datos['metodo']}  |  ARTE: {datos['arte']}"
        pdf.cell(ancho_et, 4, texto_pesca, align='C', ln=True)

        # 4. CONSERVACIÓN
        y_linea3 = pdf.get_y() + 1
        pdf.line(curr_x, y_linea3, curr_x + ancho_et, y_linea3)
        pdf.set_xy(curr_x + 2, y_linea3 + 1)
        pdf.set_font("Arial", 'B', 6.5)
        pdf.multi_cell(ancho_et - 4, 3, datos['mencion_conservacion'], align='C')

       # 5. LOTE Y FECHAS
        y_linea4 = curr_y + 58
        pdf.line(curr_x, y_linea4, curr_x + ancho_et, y_linea4)
        pdf.set_xy(curr_x + 4, y_linea4 + 1.5)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(45, 5, f"LOTE: {datos['lote']}")
        pdf.cell(45, 5, f"F. CAD: {datos['f_cad']}", align='R', ln=True)

        # Mostrar fecha de descongelación si existe
        if datos.get("f_des"):
        pdf.set_x(curr_x + 4)
        pdf.set_font("Arial", '', 8)
        pdf.cell(ancho_et - 8, 4, f"F. DESCONGELACIÓN: {datos['f_des']}", ln=True)


        # 6. EXPEDIDOR Y ÓVALO (Pie de página inamovible)
        y_linea5 = curr_y + 67
        pdf.line(curr_x, y_linea5, curr_x + ancho_et, y_linea5)
        
        pdf.set_xy(curr_x + 3, y_linea5 + 1.5)
        pdf.set_font("Arial", '', 6.5)
        # Multi_cell limitada para no pisar el óvalo
        pdf.multi_cell(62, 3, datos['expedidor_info'], align='L')

        # ÓVALO SANITARIO AJUSTADO
        pdf.ellipse(curr_x + 70, y_linea5 + 1.5, 24, 8)
        pdf.set_xy(curr_x + 70, y_linea5 + 2.8)
        pdf.set_font("Arial", 'B', 6.5)
        pdf.cell(24, 4, f"ES {datos['ovalo']} CE", align='C')


        # --- Lógica de rejilla 2x3 ---
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
        st.error("⚠️ Falta Producto o Lote.")
    else:
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        alergeno_p = limpiar_nan(prod_row["ALERGENOS"])
        
        # Trazas
        trazas_f = ""
        if alergeno_p:
            mask = df_trazas_config["ALERGENO"].astype(str).str.strip().str.upper() == alergeno_p.strip().upper()
            match = df_trazas_config[match] if 'match' in locals() else df_trazas_config[mask]
            if not match.empty:
                trazas_f = limpiar_nan(match["PUEDE_CONTENER"].iloc[0])

        # Conservación
        if "CONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR A -18ºC. UNA VEZ DESCONGELADO NO VOLVER A CONGELAR. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."
        elif "DESCONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. PRODUCTO DESCONGELADO, NO VOLVER A CONGELAR. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."
        else:
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."

        pdf_bytes = generar_pdf_a4({
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
            "f_des": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "expedidor_info": df_exped.iloc[0]["EXPEDIDOR"],
            "ovalo": df_exped.iloc[0]["OVALO_SANITARIO"]
        }, cantidad)
        
        st.success("✅ ¡Etiqueta generada con éxito!")
        st.download_button(
            label="📥 DESCARGAR PDF",
            data=pdf_bytes,
            file_name=f"etiqueta_{lote}.pdf",
            mime="application/pdf"
        )




























