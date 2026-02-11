import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF

# =========================================================
# 1. CONFIGURACIÓN Y LÓGICA DE REINICIO TOTAL
# =========================================================
st.set_page_config(page_title="Generador de Etiquetas de Santiago y Santiago", layout="wide")

# Función mejorada para limpiar TODO
def reset_campos():
    st.session_state.clear() # Borra todo el rastro de selecciones anteriores
    st.rerun()

st.markdown("""
    <style>
    .stSelectbox label, .stTextInput label, .stDateInput label, .stNumberInput label {
        font-size: 1.6rem !important; 
        font-weight: bold !important; 
        color: #1E3A8A !important;
    }
    .stButton>button { height: 3em; font-size: 1.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

def limpiar_nan(texto):
    txt = str(texto)
    return "" if txt.lower() == "nan" or not txt.strip() else txt

# =========================================================
# 2. CARGA DE DATOS
# =========================================================
SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {"PRODUCTOS": "0", "FORMAS_TRANSFORMACION": "1141842769", "ESTADOS_PRODUCTO": "57656075",
        "METODO_PRODUCCION": "1900442476", "ZONAS_FAO": "907306114", "ARTES_PESCA": "1510153858",
        "EXPEDIDORES": "1402611266"}

@st.cache_data(ttl=600)
def load_sheet(name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GIDS[name]}"
    return pd.read_csv(url)

df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_exped = load_sheet("EXPEDIDORES")

def preparar_lista(df, col_idx=None, col_name=None):
    if col_name: items = df[col_name].dropna().unique().tolist()
    else: items = df.iloc[:, col_idx].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

# =========================================================
# 3. INTERFAZ (CON ORDEN CORREGIDO Y KEYS PARA LIMPIEZA)
# =========================================================
st.title("🏷️ Generador de Etiquetas de Santiago y Santiago")

with st.sidebar:
    st.button("🔄 NUEVA ETIQUETA", on_click=reset_campos)

# FILA 1
c1, c2 = st.columns(2)
with c1: nombre_base = st.selectbox("Producto", preparar_lista(df_productos, col_name="NOMBRE_BASE"), key="k_prod")
with c2: forma = st.selectbox("Transformación", preparar_lista(df_transform, col_idx=0), key="k_trans")

# FILA 2
c3, c4 = st.columns(2)
with c3: estado = st.selectbox("Estado", preparar_lista(df_estados, col_idx=0), key="k_est")
with c4: metodo = st.selectbox("Producción", preparar_lista(df_metodo, col_idx=0), key="k_met")

# FILA 3: OPCIONALES (Zona y Arte)
zona, arte = None, None
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    c5, c6 = st.columns(2)
    with c5: zona = st.selectbox("Zona de Captura", preparar_lista(df_zonas, col_idx=0), key="k_zona")
    with c6: arte = st.selectbox("Arte de Pesca", preparar_lista(df_artes, col_idx=0), key="k_arte")

# FILA 4: LOTE
lote = st.text_input("Número de Lote", key="k_lote")

# FILA 5: FECHAS
c7, c8 = st.columns(2)
fecha_descong = None
with c7:
    if "DESCONGELADO" in str(estado).upper():
        fecha_descong = st.date_input("Fecha de Descongelación", value=date.today(), key="k_fdes")
with c8:
    def_cad = date.today()
    if "DESCONGELADO" in str(estado).upper() and fecha_descong:
        def_cad = fecha_descong + timedelta(days=3)
    fecha_cad = st.date_input("Fecha de Caducidad", value=def_cad, key="k_fcad")

cantidad = st.number_input("Número de etiquetas", min_value=1, value=1, key="k_cant")

# =========================================================
# 4. FUNCIÓN PDF (MÁS COMPACTA Y FIX DE INGREDIENTES)
# =========================================================
def generar_pdf_a4(datos, cantidad):
    pdf = FPDF()
    pdf.add_page()
    
    # ETIQUETA MÁS COMPACTA (80mm de ancho)
    ancho_et, alto_et = 80, 95
    mx, my, sep = 20, 10, 5 
    curr_x, curr_y = mx, my

    for i in range(int(cantidad)):
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # Denominación
        pdf.set_xy(curr_x, curr_y + 4)
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(ancho_et, 4, f"{datos['nombre_base'].upper()}\nPRODUCTO {datos['mencion_estado'].upper()}", align='C')
        
        # Nombre Científico
        pdf.set_xy(curr_x, curr_y + 13)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C')

        # INGREDIENTES DENTRO DEL MARCO
        pdf.line(curr_x, curr_y + 18, curr_x + ancho_et, curr_y + 18)
        if datos['ingredientes']:
            pdf.set_xy(curr_x + 3, curr_y + 19)
            long = len(datos['ingredientes'])
            f_size = 7 if long < 120 else (6 if long < 200 else 5)
            pdf.set_font("Arial", 'B', f_size)
            pdf.write(3, "INGREDIENTES: ")
            pdf.set_font("Arial", '', f_size)
            # El ancho es (ancho_et - 6) para dejar 3mm de margen a cada lado
            pdf.multi_cell(ancho_et - 6, 3, datos['ingredientes'], align='L')
        
        # CONTIENE (Alergenos)
        pdf.set_xy(curr_x + 3, curr_y + 34)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(ancho_et - 6, 4, f"CONTIENE: {str(datos['alergenos']).upper()}")

        # ZONA, MÉTODO Y ARTE (NEGRITAS)
        pdf.rect(curr_x, curr_y + 42, ancho_et, 15)
        pdf.set_font("Arial", 'B', 8)
        pdf.set_xy(curr_x + 3, curr_y + 43); pdf.write(4, "ZONA DE CAPTURA: "); pdf.set_font("Arial", '', 8); pdf.write(4, f"{datos['zona']}")
        pdf.set_xy(curr_x + 3, curr_y + 47.5); pdf.set_font("Arial", 'B', 8); pdf.write(4, "MÉTODO DE PESCA: "); pdf.set_font("Arial", '', 8); pdf.write(4, f"{datos['metodo']}")
        pdf.set_xy(curr_x + 3, curr_y + 52); pdf.set_font("Arial", 'B', 8); pdf.write(4, "ARTE DE PESCA: "); pdf.set_font("Arial", '', 8); pdf.write(4, f"{datos['arte']}")

        # LOTE Y FECHAS
        pdf.rect(curr_x, curr_y + 68, ancho_et, 13)
        pdf.set_xy(curr_x + 3, curr_y + 69); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 5, f"LOTE: {datos['lote']}")
        pdf.set_xy(curr_x + 3, curr_y + 75); pdf.set_font("Arial", 'B', 9)
        f_desc = f"  DESCONG: {datos['f_des']}" if datos['f_des'] else ""
        pdf.cell(0, 5, f"CAD: {datos['f_cad']}{f_desc}")

        # Óvalo y Empresa
        pdf.ellipse(curr_x + 58, curr_y + 82, 18, 10)
        pdf.set_xy(curr_x + 58, curr_y + 83); pdf.set_font("Arial", 'B', 6); pdf.cell(18, 2, "ES", align='C', ln=True)
        pdf.set_x(curr_x + 58); pdf.cell(18, 2, str(datos['ovalo']), align='C', ln=True)
        pdf.set_x(curr_x + 58); pdf.cell(18, 2, "CE", align='C')

        if (i + 1) % 2 == 0: curr_x = mx; curr_y += alto_et + sep
        else: curr_x += ancho_et + sep
        if (i + 1) % 6 == 0 and (i + 1) < cantidad: pdf.add_page(); curr_x, curr_y = mx, my
            
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 5. BOTÓN GENERAR
# =========================================================
if st.button("🚀 GENERAR ETIQUETAS"):
    if nombre_base == "Selecciona una opción" or not lote:
        st.error("⚠️ Falta algún campo por rellenar, revisa bien.")
    else:
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        
        # --- PRIMERO: Calculamos la lógica de conservación ---
        if "CONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR A -18ºC. UNA VEZ DESCONGELADO NO VOLVER A CONGELAR. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."
        elif "DESCONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. PRODUCTO DESCONGELADO, NO VOLVER A CONGELAR. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."
        else:  # Para producto FRESCO
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."

        # --- SEGUNDO: Generamos el PDF pasando la variable ya calculada ---
        pdf_bytes = generar_pdf_a4({
            "nombre_base": f"{nombre_base} {forma if forma != 'Selecciona una opción' else ''}",
            "mencion_estado": estado,
            "nombre_cientifico": prod_row["NOMBRE_CIENTIFICO"],
            "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
            "alergenos": limpiar_nan(prod_row["ALERGENOS"]),
            "mencion_conservacion": mencion_cons, # Aquí usamos la variable de arriba
            "metodo": metodo, 
            "lote": lote, 
            "zona": zona if zona else "N/A", 
            "arte": arte if arte else "N/A",
            "f_cad": fecha_cad.strftime("%d/%m/%Y"), 
            "f_des": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "ovalo": df_exped.iloc[0]["OVALO_SANITARIO"]
        }, cantidad)

        st.success("✅ Hecho.")
        st.download_button("📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"etiqueta_{lote}.pdf", mime="application/pdf")


