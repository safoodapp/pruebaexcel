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
# 4. EDICIÓN DE ETIQUETA (ACTUALIZADO A 100x150mm)
# =========================================================
def generar_pdf_vrittech(datos, cantidad, ancho_mm=100, alto_mm=150):
    # Definimos el tamaño de la etiqueta en mm
    ancho_et, alto_et = 100, 150
    
    # Creamos el PDF con el tamaño exacto de la etiqueta
    pdf = FPDF(orientation='P', unit='mm', format=(ancho_et, alto_et))
    pdf.set_auto_page_break(auto=False)
    
    for i in range(int(cantidad)):
        pdf.add_page()
        
        # Coordenadas base (márgenes internos)
        mx = 5 
        ancho_util = ancho_et - (mx * 2)
        
        # 1. CABECERA
        pdf.set_xy(mx, 8)
        pdf.set_font("Arial", 'B', 14) # Aumentamos fuente por el tamaño 100x150
        pdf.multi_cell(ancho_util, 6, datos['nombre_base'].upper(), align='C')
        
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(ancho_util, 6, f"({datos['nombre_cientifico']})", align='C', ln=True)
        
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(ancho_util, 7, f"PRODUCTO {datos['mencion_estado'].upper()}", align='C', ln=True)

        # SEPARADOR 1 (Cabecera) - Bajamos la línea a 35mm
        y_linea = 35
        pdf.line(mx, y_linea, ancho_et - mx, y_linea)

        # 2. INGREDIENTES Y ALÉRGENOS
        pdf.set_xy(mx + 2, y_linea + 4)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(25, 4, "INGREDIENTES:", ln=0)
        pdf.set_font("Arial", '', 8.5)
        pdf.multi_cell(ancho_util - 25, 4, f" {datos['ingredientes']}", align='J')
        
        pdf.ln(2)
        pdf.set_x(mx + 2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(ancho_util, 5, f"CONTIENE: {str(datos['alergenos']).upper()}", ln=True)
        
        if datos['trazas']:
            pdf.set_x(mx + 2)
            pdf.set_font("Arial", 'I', 8.5)
            pdf.multi_cell(ancho_util, 4, f"Puede contener trazas de: {datos['trazas']}", align='L')

        # 3. DATOS DE PESCA (Fijo en 75mm)
        y_sep2 = 75
        pdf.line(mx, y_sep2, ancho_et - mx, y_sep2)
        pdf.set_xy(mx + 2, y_sep2 + 3)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(ancho_util, 6, f"ZONA DE CAPTURA: {datos['zona']}", ln=True)
        pdf.cell(ancho_util, 6, f"MÉTODO DE PESCA: {datos['metodo']}", ln=True)
        pdf.cell(ancho_util, 6, f"ARTE DE PESCA: {datos['arte']}", ln=True)

        # 4. CONSERVACIÓN (Fijo en 100mm)
        y_sep3 = 100
        pdf.line(mx, y_sep3, ancho_et - mx, y_sep3)
        pdf.set_xy(mx + 2, y_sep3 + 4)
        pdf.set_font("Arial", 'B', 9)
        pdf.multi_cell(ancho_util, 4.5, datos['mencion_conservacion'], align='C')

        # 5. LOTE Y FECHAS (Fijo en 120mm)
        y_sep4 = 120
        pdf.line(mx, y_sep4, ancho_et - mx, y_sep4)
        pdf.set_xy(mx + 2, y_sep4 + 4)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(45, 8, f"LOTE: {datos['lote']}")
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(40, 8, f"F. CAD: {datos['f_cad']}", align='R', ln=True)
        
        if datos.get("f_des"):
            pdf.set_x(mx + 2)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(ancho_util, 6, f"F. DESCONGELACIÓN: {datos['f_des']}", ln=True, align='C')

        # 6. PIE Y ÓVALO (Fijo en 138mm)
        y_sep5 = 138
        pdf.line(mx, y_sep5, ancho_et - mx, y_sep5)
        
        # Óvalo Sanitario (Más grande para que se lea bien)
        x_oval, y_oval = ancho_et - 35, y_sep5 + 1.5
        pdf.ellipse(x_oval, y_oval, 25, 9)
        pdf.set_font("Arial", 'B', 6.5)
        pdf.set_xy(x_oval, y_oval + 1)
        pdf.cell(25, 2.5, "ES", align='C', ln=True)
        pdf.set_x(x_oval)
        pdf.cell(25, 2.5, datos['ovalo'], align='C', ln=True)
        pdf.set_x(x_oval)
        pdf.cell(25, 2.5, "CE", align='C')

        # Datos Expedidor
        pdf.set_xy(mx + 2, y_sep5 + 2)
        pdf.set_font("Arial", '', 7)
        pdf.multi_cell(ancho_util - 30, 3, datos['expedidor_info'], align='L')

    return pdf.output(dest='S').encode('latin-1', errors='ignore')      
# =========================================================
# 5. BOTÓN GENERAR (CÓDIGO FINAL LISTO PARA COPIAR)
# =========================================================
if st.button("🚀 GENERAR ETIQUETAS"):
    if nombre_base == "Selecciona una opción" or not lote:
        st.error("⚠️ Falta seleccionar el Producto o escribir el Lote.")
    else:
        # 1. Buscamos los datos del producto en el DataFrame
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        alergeno_p = limpiar_nan(prod_row["ALERGENOS"])
        
        # 2. Lógica de Trazas
        trazas_f = ""
        if alergeno_p:
            mask = df_trazas_config["ALERGENO"].astype(str).str.strip().str.upper() == alergeno_p.strip().upper()
            match_df = df_trazas_config[mask]
            if not match_df.empty:
                trazas_f = limpiar_nan(match_df["PUEDE_CONTENER"].iloc[0])

        # 3. Lógica de Conservación según el estado
        if "CONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR A -18ºC. UNA VEZ DESCONGELADO NO VOLVER A CONGELAR. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."
        elif "DESCONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. PRODUCTO DESCONGELADO, NO VOLVER A CONGELAR. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."
        else:
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."

        # 4. LLAMADA A LA FUNCIÓN (Aquí es donde pasamos los datos reales)
        # Puedes cambiar 100 y 150 por el tamaño real de tu etiqueta Vrittech
        pdf_bytes = generar_pdf_vrittech({
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
        }, cantidad, ancho_mm=100, alto_mm=150) # <--- AJUSTA EL TAMAÑO AQUÍ
        
        st.success(f"✅ ¡{cantidad} etiqueta(s) generada(s) con éxito!")
        st.download_button(
            label="📥 DESCARGAR PDF PARA IMPRIMIR",
            data=pdf_bytes,
            file_name=f"etiqueta_{lote}.pdf",
            mime="application/pdf"
        )













































