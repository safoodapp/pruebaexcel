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
# 4. GENERACIÓN DE PDF Y LÓGICA DE ALÉRGENOS
# =========================================================
def generar_pdf(datos, cantidad):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    # ... (Aquí va tu estructura de diseño de celdas pdf.rect, pdf.cell, etc.)
    # Por brevedad se omite el diseño visual repetitivo, pero usa los campos:
    # datos['nombre_completo'], datos['mencion_conservacion'], datos['trazas'], etc.
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
