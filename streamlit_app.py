import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF

# =========================================================
# 1. CONFIGURACIÓN Y FUNCIONES DE APOYO
# =========================================================
st.set_page_config(page_title="Generador Etiquetas RD 1082/2025", layout="centered")

def limpiar_nan(texto):
    txt = str(texto)
    return "" if txt.lower() == "nan" or not txt.strip() else txt

def obtener_genero(nombre_base):
    femeninos = ["MERLUZA", "GAMBA", "POTA", "DORADA", "LUBINA", "TRUCHA", "CORVINA", "PIJOTA", "PESCADILLA", "TINTORERA"]
    return "F" if any(f in nombre_base.upper() for f in femeninos) else "M"

def ajustar_genero(texto, genero):
    if genero == "F":
        return texto.replace("ado", "ada").replace("ero", "era").replace("ido", "ida").replace("descongelado", "descongelada")
    return texto

# =========================================================
# 2. CARGA DE DATOS (GOOGLE SHEETS)
# =========================================================
SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {
    "PRODUCTOS": "0", "FORMAS_TRANSFORMACION": "1141842769", "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476", "ZONAS_FAO": "907306114", "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266", "TRAZAS_CONFIG": "1059656739",
}

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
# 3. INTERFAZ DE USUARIO (SIMPLIFICADA)
# =========================================================
st.title("Generador Etiquetas RD 1082/2025")

# Inicialización de variables para evitar NameError
zona, arte, fecha_descong = None, None, None

col1, col2 = st.columns(2)
with col1:
    nombre_base = st.selectbox("Producto", preparar_lista(df_productos, col_name="NOMBRE_BASE"))
    forma = st.selectbox("Transformación", preparar_lista(df_transform, col_idx=0))
    estado = st.selectbox("Estado", preparar_lista(df_estados, col_idx=0))
    lote = st.text_input("Número de Lote")

with col2:
    metodo = st.selectbox("Producción", preparar_lista(df_metodo, col_idx=0))
    fecha_cad = st.date_input("Caducidad")
    cantidad = st.number_input("Etiquetas", min_value=1, value=1)
    # Expedidor automático, no se muestra en interfaz
    expedidor_auto = df_exped.iloc[0]["EXPEDIDOR"]
    ovalo_auto = df_exped.iloc[0]["OVALO_SANITARIO"]

# Campos condicionales
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    c3, c4 = st.columns(2)
    with c3: zona = st.selectbox("Zona FAO", preparar_lista(df_zonas, col_idx=0))
    with c4: arte = st.selectbox("Arte", preparar_lista(df_artes, col_idx=0))

if "DESCONGELADO" in str(estado).upper():
    fecha_descong = st.date_input("Fecha de Descongelación", value=date.today())

# =========================================================
# FUNCIÓN DE DIBUJO PDF (Pon esto ANTES del botón de generar)
# =========================================================
def generar_pdf_a4(datos, cantidad):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    ancho_et, alto_et = 95, 95
    mx, my = 7, 10
    curr_x, curr_y = mx, my

    for i in range(int(cantidad)):
        # Marco exterior limpio
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # BLOQUE 1: Denominación y Mención de Estado (Fijo)
        pdf.set_xy(curr_x, curr_y + 3)
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(ancho_et, 5, datos['nombre_base'].upper(), align='C')
        
        pdf.set_font("Arial", 'B', 9)
        pdf.set_xy(curr_x, curr_y + 10)
        pdf.cell(ancho_et, 4, f"PRODUCTO {datos['mencion_estado'].upper()}", align='C')
        
        pdf.set_font("Arial", 'I', 8)
        pdf.set_xy(curr_x, curr_y + 14)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C')

        # BLOQUE 2: Ingredientes, CONTIENE y Trazas (Posición Fija)
        pdf.line(curr_x, curr_y + 20, curr_x + ancho_et, curr_y + 20)
        pdf.set_xy(curr_x + 2, curr_y + 21)
        
        if datos['ingredientes']:
            pdf.set_font("Arial", 'B', 7)
            pdf.write(3, "INGREDIENTES: ")
            pdf.set_font("Arial", '', 7)
            pdf.write(3, datos['ingredientes'])
        
        # Alérgenos y Trazas juntos
        pdf.set_xy(curr_x + 2, curr_y + 33)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(ancho_et, 4, f"CONTIENE: {str(datos['alergenos']).upper()}")
        
        if datos['trazas']:
            pdf.set_xy(curr_x + 2, curr_y + 37)
            pdf.set_font("Arial", 'I', 7)
            pdf.cell(ancho_et, 4, f"Puede contener: {datos['trazas']}")

        # BLOQUE 3: Origen y Método
        pdf.rect(curr_x, curr_y + 42, ancho_et, 15)
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(curr_x + 3, curr_y + 43)
        pdf.cell(0, 4, f"- ZONA: {datos['zona'] if datos['zona'] else 'N/A'}")
        pdf.set_xy(curr_x + 3, curr_y + 47)
        pdf.cell(0, 4, f"- METODO: {datos['metodo']}")
        pdf.set_xy(curr_x + 3, curr_y + 51)
        pdf.cell(0, 4, f"- ARTE DE PESCA: {datos['arte'] if datos['arte'] else 'N/A'}")

        # BLOQUE 4: Conservación
        pdf.rect(curr_x, curr_y + 57, ancho_et, 10)
        pdf.set_xy(curr_x + 2, curr_y + 58)
        pdf.set_font("Arial", 'B', 7)
        pdf.multi_cell(ancho_et - 4, 3.5, datos['mencion_conservacion'].upper(), align='C')

        # BLOQUE 5: Trazabilidad (Lote y Fechas)
        pdf.rect(curr_x, curr_y + 68, ancho_et, 13)
        pdf.set_xy(curr_x + 3, curr_y + 69)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 4, f"LOTE: {datos['lote']}")
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(curr_x + 3, curr_y + 75)
        f_desc_txt = f"   DESCONG: {datos['f_descong']}" if datos['f_descong'] else ""
        pdf.cell(0, 4, f"CAD: {datos['f_cad']}{f_desc_txt}")

        # BLOQUE 6: Empresa y Óvalo
        pdf.set_xy(curr_x + 2, curr_y + 82)
        pdf.set_font("Arial", '', 6)
        pdf.multi_cell(ancho_et - 25, 2.8, f"{datos['expedidor']}\nCalle Laguna del Marquesado 43C, Nave 43C\n28021 Madrid")
        
        pdf.ellipse(curr_x + 72, curr_y + 82, 18, 11)
        pdf.set_xy(curr_x + 72, curr_y + 83.5)
        pdf.set_font("Arial", 'B', 6)
        pdf.cell(18, 2.5, "ES", align='C', ln=True)
        pdf.cell(18, 2.5, str(datos['ovalo']), align='C', ln=True)
        pdf.cell(18, 2.5, "CE", align='C')
# Lógica para organizar 6 etiquetas por página (2 columnas x 3 filas)
        if (i + 1) % 2 == 0:
            curr_x = mx
            curr_y += alto_et + 2
        else:
            curr_x += ancho_et + 2
            
        if (i + 1) % 6 == 0 and (i + 1) < cantidad:
            pdf.add_page()
            curr_x, curr_y = mx, my
            
    return pdf.output(dest='S').encode('latin-1')
if st.button("🚀 GENERAR ETIQUETAS"):
    # Comprobación de campos obligatorios
    campos_obligatorios = {
        "Producto": nombre_base,
        "Transformación": forma,
        "Estado": estado,
        "Producción": metodo,
        "Lote": lote
    }
    
    faltan = [k for k, v in campos_obligatorios.items() if v == "Selecciona una opción" or not str(v).strip()]
    
    if faltan:
        st.error(f"⚠️ No se puede generar la etiqueta. Faltan estos campos obligatorios: {', '.join(faltan)}")
    else:
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        
        # Mención de conservación dinámica
        mencion_cons = "CONSERVAR ENTRE 0 Y 4ºC"
        if "DESCONGELADO" in estado.upper():
            mencion_cons = "PRODUCTO DESCONGELADO. NO VOLVER A CONGELAR. CONSERVAR A -18ºC"
        elif "CONGELADO" in estado.upper():
            mencion_cons = "UNA VEZ DESCONGELADO NO VOLVER A CONGELAR. CONSERVAR A -18ºC"

        # Lookup de trazas
        alergeno_p = limpiar_nan(prod_row["ALERGENOS"])
        trazas_f = ""
        if alergeno_p:
            mask = df_trazas_config["ALERGENO"].astype(str).str.strip().str.upper() == alergeno_p.strip().upper()
            match = df_trazas_config[mask]
            if not match.empty:
                trazas_f = limpiar_nan(match["PUEDE_CONTENER"].iloc[0])

        info_etiqueta = {
            "nombre_base": f"{nombre_base} {forma}",
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
            "f_descong": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "expedidor": expedidor_auto,
            "ovalo": ovalo_auto
        }

        pdf_bytes = generar_pdf_a4(info_etiqueta, cantidad)
        st.success("✅ Etiqueta creada correctamente.")
        st.download_button("📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"etiqueta_{lote}.pdf", mime="application/pdf")

