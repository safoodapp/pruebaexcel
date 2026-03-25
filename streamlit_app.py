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
st.title("🏷️ Generador de Etiquetas Santiago y Santiago")

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

        # CABECERA (Producto y Lote) - Se queda igual, está perfecta
        pdf.set_xy(mx, 10)
        pdf.set_font("Arial", 'B', 15)
        txt_prod = f"{datos['nombre_base']}".strip()
        pdf.multi_cell(55, 7, txt_prod.upper(), align='L')
        
        pdf.set_x(mx)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(55, 5, f"({datos['nombre_cientifico']})", ln=True)
        
        pdf.set_x(mx)
        pdf.set_font("Arial", '', 11)
        pdf.cell(55, 5, f"producto {datos['forma'].lower()}", ln=True)

        pdf.set_line_width(0.4)
        pdf.rect(65, 10, 28, 20)
        pdf.set_xy(65, 12)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(28, 5, "LOTE:", align='C', ln=True)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_x(65)
        pdf.cell(28, 8, datos['lote'], align='C')
        
        # CUERPO DINÁMICO
        pdf.set_line_width(0.2)
        pdf.line(mx, 35, 100-mx, 35)
        
        y_pos = 38
        if datos['ingredientes']:
            pdf.set_xy(mx, y_pos)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(25, 5, "INGREDIENTES: ", ln=0)
            pdf.set_font("Arial", '', 9)
            # Usamos multi_cell con un interlineado un poco menor (4) para ahorrar espacio
            pdf.multi_cell(ancho_util - 25, 4, datos['ingredientes'], align='C')
            y_pos = pdf.get_y() + 2

        pdf.set_xy(mx, y_pos)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(ancho_util, 6, f"CONTIENE: {str(datos['alergenos']).upper()}", ln=True)
        
        if datos['trazas']:
            pdf.set_x(mx)
            pdf.set_font("Arial", 'I', 8)
            pdf.multi_cell(ancho_util, 4, f"Puede contener trazas de: {datos['trazas']}", align='L')
        
        # --- BLOQUE TRAZABILIDAD (Bajamos un poco para que no se pise) ---
        y_pos = 72 
        pdf.line(mx, y_pos, 100-mx, y_pos)
        y_pos += 3
        pdf.set_xy(mx, y_pos)
        pdf.set_font("Arial", 'B', 10)
        
        if "acuicultura" not in str(datos['metodo']).lower():
            # ZONA DE CAPTURA
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(pdf.get_string_width("ZONA DE CAPTURA: "), 5, "ZONA DE CAPTURA: ", align='L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 5, datos['zona'], ln=True, align='L')
            pdf.set_x(mx)
            
            # ARTE DE PESCA
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(pdf.get_string_width("ARTE DE PESCA: "), 5, "ARTE DE PESCA: ", align='L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 5, datos['arte'], ln=True, align='L')
            pdf.set_x(mx)
        
        # MÉTODO DE PESCA
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(pdf.get_string_width("MÉTODO DE PESCA: "), 5, "MÉTODO DE PESCA: ", align='L')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, datos['metodo'], ln=True, align='L')
        pdf.set_x(mx)
        
        # PAÍS DE ORIGEN
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(pdf.get_string_width("PAÍS DE ORIGEN: "), 5, "PAÍS DE ORIGEN: ", align='L')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, datos['pais'], ln=True, align='L')

        # --- CONSERVACIÓN (Le damos su espacio fijo) ---
        y_pos = 98
        pdf.line(mx, y_pos, 100-mx, y_pos)
        pdf.set_xy(mx, y_pos + 3)
        pdf.set_font("Arial", 'B', 9.5)
        pdf.multi_cell(ancho_util, 4.5, datos['mencion_conservacion'], align='C')
        pdf.cell(55, 5, f"producto {datos['mencion_estado'].lower()}", ln=True)

        # --- FECHAS ---
        y_pos = 120
        pdf.line(mx, y_pos, 100-mx, y_pos)
        pdf.set_xy(mx, y_pos + 3)
        if datos['f_des']:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(ancho_util, 6, f"F. DESCONGELACIÓN: {datos['f_des']}", align='C', ln=True)
            pdf.set_x(mx)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(ancho_util, 8, f"F. CAD: {datos['f_cad']}", align='C')

        # --- PIE (Subimos 2mm para que no se corte) ---
        y_pos = 135
        pdf.line(mx, y_pos, 100-mx, y_pos)
        pdf.set_xy(mx, y_pos + 2)
        pdf.set_font("Arial", '', 7.5)
        pdf.multi_cell(ancho_util - 30, 3.5, datos['expedidor_info'])
        
        pdf.ellipse(72, y_pos + 2, 22, 9)
        pdf.set_xy(72, y_pos + 3.5)
        pdf.set_font("Arial", 'B', 6.5)
        pdf.cell(22, 2.5, "ES", align='C', ln=True)
        pdf.set_x(72)
        pdf.cell(22, 2.5, datos['ovalo'], align='C')

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
        if"DESCONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR ENTRE 0-4ºC. NO VOLVER A CONGELAR."
        elif "CONGELADO" in estado.upper():
            mencion_cons = "CONSERVAR A -18ºC, UNA VEZ DESCONGELADO NO VOLVER A CONGELAR."
      
        # DENTRO DEL BOTÓN 'GENERAR ETIQUETAS'
        pdf_bytes = generar_pdf_final({
            "nombre_base": nombre_base,
            "forma": forma if forma != "Selecciona una opción" else "",
            "nombre_cientifico": prod_row["NOMBRE_CIENTIFICO"],
            "mencion_estado": estado,
            "lote": lote,
            "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
            "alergenos": alergeno_p,
            "trazas": trazas_f,
            "metodo": metodo, 
            "zona": zona, 
            "arte": arte, 
            "pais": pais_orig,
            "mencion_conservacion": mencion_cons,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "f_des": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            # ESTA ES LA LÍNEA QUE CAUSA EL ERROR SI FALTA O ESTÁ MAL ESCRITA:
            "expedidor_info": df_exped.iloc[0]["EXPEDIDOR"] if not df_exped.empty else "PESCADOS SANTIAGO S.L.",
            "ovalo": df_exped.iloc[0]["OVALO_SANITARIO"] if not df_exped.empty else "12.345/M"
        }, cantidad)

        st.success("✅ Etiquetas listas")
        st.download_button("📥 DESCARGAR PDF", pdf_bytes, f"etiquetas_{lote}.pdf", "application/pdf")















































