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
        # Dibujar el borde
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # 1. Cabecera (Nombre y Estado)
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(curr_x, curr_y, ancho_et, 18, 'F')
        pdf.set_xy(curr_x, curr_y + 3)
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(ancho_et, 4.5, str(datos['nombre_completo']).upper(), align='C')
        pdf.set_xy(curr_x, curr_y + 13)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C')

        # 2. Ingredientes y Alérgenos
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

        # 3. Origen y Método
        pdf.rect(curr_x, curr_y + 36, ancho_et, 16)
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(curr_x + 5, curr_y + 38)
        if datos['zona']: pdf.cell(0, 4, f"- ZONA: {datos['zona']}")
        pdf.set_xy(curr_x + 5, curr_y + 42)
        pdf.cell(0, 4, f"- METODO: {datos['metodo']}")
        pdf.set_xy(curr_x + 5, curr_y + 46)
        if datos['arte']: pdf.cell(0, 4, f"- ARTE DE PESCA: {datos['arte']}")

        # 4. Conservación (RD 1082/2025)
        pdf.rect(curr_x, curr_y + 52, ancho_et, 12)
        pdf.set_xy(curr_x + 2, curr_y + 54)
        pdf.set_font("Arial", 'B', 7)
        pdf.multi_cell(ancho_et - 4, 3.5, datos['mencion_conservacion'], align='C')

        # 5. Trazabilidad y Fechas
        pdf.rect(curr_x, curr_y + 64, ancho_et, 15)
        pdf.set_xy(curr_x + 5, curr_y + 66)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 4, f"LOTE: {datos['lote']}")
        pdf.set_font("Arial", '', 8)
        pdf.set_xy(curr_x + 5, curr_y + 70)
        f_desc_txt = f"   DESCONG: {datos['f_descong']}" if datos['f_descong'] else ""
        pdf.cell(0, 4, f"CAD: {datos['f_cad']}{f_desc_txt}")

        # 6. Empresa y Óvalo Sanitario
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

        # Lógica para organizar 6 etiquetas por página (2 columnas x 3 filas)
        if (i + 1) % 2 == 0:
            curr_x = mx
            curr_y += alto_et + 3
        else:
            curr_x += ancho_et + 3
        if (i + 1) % 6 == 0 and (i + 1) < cantidad:
            pdf.add_page()
            curr_x, curr_y = mx, my
            
    return pdf.output(dest='S').encode('latin-1')
st.divider()

if st.button("🚀 GENERAR ETIQUETAS"):
    # 1. Validación: Comprobar que no faltan campos obligatorios
    campos_vacios = [nombre_base, forma, estado, metodo]
    if "Selecciona una opción" in campos_vacios or not lote.strip():
        st.warning("⚠️ ¡Atención! Rellena todos los campos obligatorios y el número de lote antes de continuar.")
    else:
        # 2. Si todo está bien, procesamos los datos
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        gen = obtener_genero(nombre_base)
        
        nombre_final = f"{nombre_base} {ajustar_genero(forma, gen)} {ajustar_genero(estado, gen)}"
        
        # Lógica de alérgenos y trazas
        alergeno_p = limpiar_nan(prod_row["ALERGENOS"])
        trazas_f = ""
        if alergeno_p:
            mask = df_trazas_config["ALERGENO"].astype(str).str.strip().str.upper() == alergeno_p.strip().upper()
            match = df_trazas_config[mask]
            if not match.empty:
                trazas_f = limpiar_nan(match["PUEDE_CONTENER"].iloc[0])

        # Mención de conservación
        mencion = "CONSERVAR ENTRE 0 Y 4ºC"
        if "DESCONGELADO" in estado.upper():
            mencion = "PRODUCTO DESCONGELADO. NO VOLVER A CONGELAR. CONSERVAR A -18ºC"
        elif "CONGELADO" in estado.upper():
            mencion = "UNA VEZ DESCONGELADO NO VOLVER A CONGELAR. CONSERVAR A -18ºC"

        info_etiqueta = {
            "nombre_completo": nombre_final,
            "nombre_cientifico": prod_row["NOMBRE_CIENTIFICO"],
            "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
            "alergenos": alergeno_p,
            "trazas": trazas_f,
            "mencion_conservacion": mencion,
            "metodo": metodo, 
            "lote": lote,
            "zona": zona if zona != "Selecciona una opción" else None,
            "arte": arte if arte != "Selecciona una opción" else None,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "f_descong": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "expedidor": expedidor_auto,
            "ovalo": ovalo_auto
        }

        # 3. Generar el PDF
        pdf_bytes = generar_pdf_a4(info_etiqueta, cantidad)

        # 4. Mostrar mensajes de éxito y botón de descarga
        st.success("✅ ¡Etiqueta creada correctamente! Ya puedes descargarla aquí debajo:")
        
        st.download_button(
            label="📥 DESCARGAR PDF",
            data=pdf_bytes,
            file_name=f"etiqueta_{lote}.pdf",
            mime="application/pdf"
        )

