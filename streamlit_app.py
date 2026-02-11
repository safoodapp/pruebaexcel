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
# 2. CARGA DE DATOS (ttl=60 para ver cambios rápido)
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
# 3. INTERFAZ Y BOTÓN LIMPIAR
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
# 4. FUNCIÓN PDF (CORRECCIÓN FINAL DE MÁRGENES Y ÓVALO)
# =========================================================
def generar_pdf_a4(datos, cantidad):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    
    ancho_et, alto_et = 102, 76
    mx, my, sep = 5, 10, 5 
    curr_x, curr_y = mx, my

    for i in range(int(cantidad)):
        # 1. RECUADRO PRINCIPAL
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # 2. CABECERA
        pdf.set_xy(curr_x, curr_y + 4)
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(ancho_et, 5, datos['nombre_base'].upper(), align='C')
        
        pdf.set_font("Arial", 'I', 9)
        pdf.set_x(curr_x)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C', ln=True)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_x(curr_x)
        pdf.cell(ancho_et, 5, f"PRODUCTO {datos['mencion_estado'].upper()}", align='C', ln=True)

        # 3. SECCIÓN INGREDIENTES (RESTRINGIDO PARA QUE NO SE SALGA)
        pdf.line(curr_x + 2, curr_y + 22, curr_x + ancho_et - 2, curr_y + 22)
        
        # Ajustamos el cursor y limitamos el ancho a 96mm para dejar margen derecho
        pdf.set_xy(curr_x + 3, curr_y + 23)
        pdf.set_font("Arial", 'B', 8)
        
        # Usamos multi_cell para TODO el bloque de ingredientes para controlar el ancho
        ing_texto = f"INGREDIENTES: {datos['ingredientes'] if datos['ingredientes'] else 'No contiene.'}"
        pdf.multi_cell(95, 3.8, ing_texto, align='L')
        
        # Alérgenos y Trazas
        pdf.set_x(curr_x + 3)
        pdf.set_font("Arial", 'B', 9) # Un poco más grande para que destaque
        pdf.multi_cell(95, 4.5, f"CONTIENE: {str(datos['alergenos']).upper()}", align='L')
        
        if datos['trazas'] and str(datos['trazas']).lower() != "nan":
            pdf.set_x(curr_x + 3)
            pdf.set_font("Arial", 'I', 8)
            pdf.multi_cell(95, 4, f"Puede contener: {str(datos['trazas']).upper()}", align='L')

        # 4. DATOS DE PESCA
        pdf.line(curr_x + 2, curr_y + 48, curr_x + ancho_et - 2, curr_y + 48)
        pdf.set_xy(curr_x + 3, curr_y + 49)
        pdf.set_font("Arial", 'B', 8)
        # Combinamos en una sola línea controlada
        pesca_info = f"ZONA: {datos['zona']}  MÉTODO: {datos['metodo']}  ARTE: {datos['arte']}"
        pdf.cell(95, 4, pesca_info, ln=True)
        
        # 5. CONSERVACIÓN
        pdf.set_x(curr_x + 3)
        pdf.set_font("Arial", 'B', 7)
        pdf.multi_cell(ancho_et - 6, 3.5, datos['mencion_conservacion'], align='C')

        # 6. LOTE Y CADUCIDAD
        pdf.line(curr_x + 2, curr_y + 62, curr_x + ancho_et - 2, curr_y + 62)
        pdf.set_xy(curr_x + 3, curr_y + 63)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(45, 7, f"LOTE: {datos['lote']}")
        
        pdf.set_font("Arial", 'B', 10)
        f_cad_completa = f"F. CAD: {datos['f_cad']}"
        if datos['f_des']: f_cad_completa += f" (D: {datos['f_des']})"
        pdf.cell(50, 7, f_cad_completa, align='R', ln=True)

        # 7. EXPEDIDOR Y ÓVALO (REPOSICIONADO PARA NO PISARSE)
        pdf.line(curr_x + 2, curr_y + 70, curr_x + ancho_et - 2, curr_y + 70)
        
        # Datos empresa a la izquierda
        pdf.set_xy(curr_x + 2, curr_y + 71)
        pdf.set_font("Arial", '', 6)
        pdf.multi_cell(70, 2.2, f"{datos['expedidor_info']}", align='L')

        # Óvalo Sanitario a la derecha (ajustado para que no toque las letras)
        pdf.ellipse(curr_x + 78, curr_y + 71, 18, 4.2)
        pdf.set_xy(curr_x + 78, curr_y + 71.5)
        pdf.set_font("Arial", 'B', 5.5)
        pdf.cell(18, 3, f"ES {datos['ovalo']} CE", align='C')

        # Lógica de rejilla A4
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
# 5. BOTÓN GENERAR (CORRECCIÓN DE ERROR DE COLUMNA Y TRAZAS)
# =========================================================
if st.button("🚀 GENERAR ETIQUETAS"):
    if nombre_base == "Selecciona una opción" or not lote:
        st.error("⚠️ Falta algún campo sin rellenar, revisalo.")
    else:
        # 1. Extraemos los datos del producto
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        alergeno_principal = limpiar_nan(prod_row["ALERGENOS"])
        
        # 2. BÚSQUEDA DE TRAZAS (Con limpieza de nombres de columna)
        trazas_final = ""
        if alergeno_principal:
            # Limpiamos los nombres de las columnas por si tienen espacios invisibles
            df_trazas_config.columns = df_trazas_config.columns.str.strip().str.upper()
            
            # Verificamos si la columna existe tras la limpieza
            col_busqueda = "ALERGENO"
            if col_busqueda in df_trazas_config.columns:
                mask = df_trazas_config[col_busqueda].astype(str).str.strip().upper() == alergeno_principal.strip().upper()
                match = df_trazas_config[mask]
                if not match.empty:
                    # Buscamos la columna de resultado (asumiendo que se llama PUEDE_CONTENER)
                    col_res = "PUEDE_CONTENER"
                    if col_res in df_trazas_config.columns:
                        trazas_final = limpiar_nan(match[col_res].iloc[0])
            else:
                st.warning(f"No encontré la columna '{col_busqueda}' en la hoja de trazas. Revisa el Excel.")

        # 3. Lógica de Conservación
        if "CONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR A -18ºC. UNA VEZ DESCONGELADO NO VOLVER A CONGELAR. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."
        elif "DESCONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. PRODUCTO DESCONGELADO, NO VOLVER A CONGELAR. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."
        else:
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. COCINAR COMPLETAMENTE ANTES DE CONSUMIR."

        # 4. LLAMADA AL PDF
        pdf_bytes = generar_pdf_a4({
            "nombre_base": f"{nombre_base} {forma if forma != 'Selecciona una opción' else ''}",
            "mencion_estado": estado,
            "nombre_cientifico": prod_row["NOMBRE_CIENTIFICO"],
            "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
            "alergenos": alergeno_principal,
            "trazas": trazas_final, 
            "mencion_conservacion": mencion_cons,
            "metodo": metodo, 
            "lote": lote, 
            "zona": zona if zona else "N/A", 
            "arte": arte if arte else "N/A",
            "f_cad": fecha_cad.strftime("%d/%m/%Y"), 
            "f_des": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "expedidor_info": df_exped.iloc[0]["EXPEDIDOR"], 
            "ovalo": df_exped.iloc[0]["OVALO_SANITARIO"]
        }, cantidad)
        
        st.success("✅ ¡Etiqueta generada!")
        st.download_button(
            label="📥 DESCARGAR PDF",
            data=pdf_bytes,
            file_name=f"etiqueta_{lote}.pdf",
            mime="application/pdf"
        )



















