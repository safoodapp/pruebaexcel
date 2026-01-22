import streamlit as st
import pandas as pd
from datetime import date
from fpdf import FPDF
import io

st.set_page_config(page_title="Etiquetas Pescado PRO - RD 1082/2025", layout="centered")

# =========================================================
# FUNCIONES DE SOPORTE Y LÓGICA
# =========================================================

def limpiar_nan(texto):
    txt = str(texto)
    if txt.lower() == "nan" or not txt.strip():
        return ""
    return txt

def obtener_genero(nombre_base):
    # Lista extendida de términos femeninos para concordancia
    femeninos = ["MERLUZA", "GAMBA", "POTA", "DORADA", "LUBINA", "TRUCHA", "CORVINA", "PIJOTA", "PESCADILLA", "TINTORERA", "TRUCHA"]
    if any(f in nombre_base.upper() for f in femeninos):
        return "F"
    return "M"

def ajustar_genero(texto, genero):
    if genero == "F":
        # Transformación de sufijos para concordancia femenina
        return texto.replace("ado", "ada").replace("ero", "era").replace("ido", "ida").replace("descongelado", "descongelada")
    return texto

# =========================================================
# CONFIGURACIÓN GOOGLE SHEETS
# =========================================================
SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {
    "PRODUCTOS": "0",
    "FORMAS_TRANSFORMACION": "1141842769",
    "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476",
    "ZONAS_FAO": "907306114",
    "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266",
    "TRAZAS_CONFIG": "1059656739",
}

def load_sheet(name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GIDS[name]}"
    return pd.read_csv(url)

def preparar_lista(df, col_idx=None, col_name=None):
    if col_name:
        items = df[col_name].dropna().unique().tolist()
    else:
        items = df.iloc[:, col_idx].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

# =========================================================
# FUNCIÓN GENERADORA DE PDF (ADAPTADA RD 1082/2025)
# =========================================================
def generar_pdf_a4(datos, cantidad):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    ancho_et, alto_et = 95, 95
    mx, my = 7, 10
    curr_x, curr_y = mx, my

    for i in range(cantidad):
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # Bloque 1: Cabecera (Nombre + Estado con Concordancia)
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(curr_x, curr_y, ancho_et, 18, 'F')
        pdf.set_xy(curr_x, curr_y + 3)
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(ancho_et, 4.5, str(datos['nombre_completo']).upper(), align='C')
        pdf.set_xy(curr_x, curr_y + 13)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C')

        # Bloque 2: Ingredientes y Alérgenos (Reglamento 1169)
        pdf.rect(curr_x, curr_y + 18, ancho_et, 18)
        y_int = curr_y + 19
        
        if datos['ingredientes']:
            pdf.set_font("Arial", 'B', 7)
            pdf.set_xy(curr_x + 2, y_int)
            pdf.cell(20, 3, "INGREDIENTES:")
            pdf.set_font("Arial", '', 7)
            pdf.multi_cell(ancho_et - 22, 3, datos['ingredientes'])
            y_int = pdf.get_y() + 1

        pdf.set_font("Arial", 'B', 8)
        pdf.set_xy(curr_x + 2, y_int)
        pdf.cell(ancho_et - 4, 3, f"CONTIENE: {str(datos['alergenos']).upper()}", ln=True)
        
        if datos['trazas']:
            pdf.set_font("Arial", 'I', 7)
            pdf.set_x(curr_x + 2)
            pdf.cell(ancho_et - 4, 3, f"Puede contener: {datos['trazas']}")

        # Bloque 3: Origen
        pdf.rect(curr_x, curr_y + 36, ancho_et, 16)
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(curr_x + 5, curr_y + 38)
        if datos['zona']: pdf.cell(0, 4, f"- ZONA: {datos['zona']}")
        pdf.set_xy(curr_x + 5, curr_y + 42)
        pdf.cell(0, 4, f"- METODO: {datos['metodo']}")
        pdf.set_xy(curr_x + 5, curr_y + 46)
        if datos['arte']: pdf.cell(0, 4, f"- ARTE DE PESCA: {datos['arte']}")

        # Bloque 4: Conservación y Seguridad
        pdf.rect(curr_x, curr_y + 52, ancho_et, 12)
        pdf.set_xy(curr_x + 2, curr_y + 54)
        pdf.set_font("Arial", 'B', 7)
        pdf.multi_cell(ancho_et - 4, 3.5, datos['mencion_conservacion'], align='C')

        # Bloque 5: Trazabilidad
        pdf.rect(curr_x, curr_y + 64, ancho_et, 15)
        pdf.set_xy(curr_x + 5, curr_y + 66)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 4, f"LOTE: {datos['lote']}")
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(curr_x + 5, curr_y + 70)
        pdf.cell(0, 4, f"CAD: {datos['f_cad']}   {f'DESCONG: {datos['f_descong']}' if datos['f_descong'] else ''}")

        # Bloque 6: Empresa y Óvalo
        pdf.rect(curr_x, curr_y + 79, ancho_et, 16)
        pdf.set_font("Arial", '', 6)
        pdf.set_xy(curr_x + 2, curr_y + 81)
        pdf.multi_cell(ancho_et - 30, 3, f"{datos['expedidor']}\nCalle Laguna del Marquesado 43C, Nave 43C\n28021 Madrid")
        
        pdf.ellipse(curr_x + 70, curr_y + 81, 20, 12)
        pdf.set_xy(curr_x + 70, curr_y + 83)
        pdf.set_font("Arial", 'B', 6)
        pdf.cell(20, 3, "ES", align='C', ln=True)
        pdf.set_xy(curr_x + 70, curr_y + 85)
        pdf.cell(20, 3, str(datos['ovalo']), align='C', ln=True)
        pdf.set_xy(curr_x + 70, curr_y + 87)
        pdf.cell(20, 3, "CE", align='C')

        if (i + 1) % 2 == 0:
            curr_x = mx
            curr_y += alto_et + 3
        else:
            curr_x += ancho_et + 3
        if (i + 1) % 6 == 0 and (i + 1) < cantidad:
            pdf.add_page()
            curr_x, curr_y = mx, my
            
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# CARGA DE DATOS Y APP
# =========================================================
df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_exped = load_sheet("EXPEDIDORES")
df_trazas_config = load_sheet("TRAZAS_CONFIG")

st.title("Generador Etiquetas RD 1082/2025")

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
    expedidor = st.selectbox("Expedidor", preparar_lista(df_exped, col_name="EXPEDIDOR"))

zona = st.selectbox("Zona FAO", preparar_lista(df_zonas, col_idx=0)) if "acuicultura" not in str(metodo).lower() else None
arte = st.selectbox("Arte", preparar_lista(df_artes, col_idx=0)) if "acuicultura" not in str(metodo).lower() else None

# =========================================================
# BLOQUE FINAL CORREGIDO: COPIA DESDE AQUÍ HASTA EL FINAL
# =========================================================

if st.button("🚀 GENERAR ETIQUETAS"):
    if "Selecciona una opción" not in [nombre_base, forma, estado, metodo]:
        # 1. Obtener los datos del producto seleccionado
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        
        # 2. Lógica de Género (Detectar si es Merluza, Gamba, etc.)
        gen = obtener_genero(nombre_base)
        
        # 3. Aplicar Concordancia (Transformación + Estado)
        forma_adj = ajustar_genero(forma, gen)
        estado_adj = ajustar_genero(estado, gen)
        nombre_final = f"{nombre_base} {forma_adj} {estado_adj}"
        
        # 4. Cruce con la tabla de TRAZAS_CONFIG
        alergeno_principal = limpiar_nan(prod_row["ALERGENOS"])
        trazas_final = ""
        
        if alergeno_principal:
            # Buscamos en la hoja TRAZAS_CONFIG la fila donde la columna ALERGENO coincida
            mask = df_trazas_config["ALERGENO"].astype(str).str.strip().str.upper() == alergeno_principal.strip().upper()
            match = df_trazas_config[mask]
            
            if not match.empty:
                trazas_final = limpiar_nan(match["PUEDE_CONTENER"].iloc[0])

        # 5. Lógica de Conservación por Temperaturas (RD 1082/2025)
        mencion = "CONSERVAR ENTRE 0 Y 4ºC"
        if "descongelado" in estado.lower():
            mencion = "PRODUCTO DESCONGELADO. NO VOLVER A CONGELAR. CONSERVAR A -18ºC"
        elif "congelado" in estado.lower():
            mencion = "UNA VEZ DESCONGELADO NO VOLVER A CONGELAR. CONSERVAR A -18ºC"

        # 6. Preparar diccionario de datos para el PDF
        info_etiqueta = {
            "nombre_completo": nombre_final,
            "nombre_cientifico": prod_row["NOMBRE_CIENTIFICO"],
            "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
            "alergenos": alergeno_principal,
            "trazas": trazas_final,
            "mencion_conservacion": mencion,
            "metodo": metodo, 
            "lote": lote,
            "zona": zona if zona != "Selecciona una opción" else None,
            "arte": arte if arte != "Selecciona una opción" else None,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "f_descong": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "expedidor": expedidor,
            "ovalo": df_exped[df_exped["EXPEDIDOR"] == expedidor]["OVALO_SANITARIO"].iloc[0]
        }
        
        # 7. Generar y Descargar
        pdf_bytes = generar_pdf_a4(info_etiqueta, cantidad)
        st.download_button(
            label="📥 DESCARGAR PDF",
            data=pdf_bytes,
            file_name=f"etiqueta_{lote}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("⚠️ Por favor, rellena todos los campos obligatorios antes de generar.")
