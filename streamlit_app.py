

import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Etiquetas pescado", layout="centered")

# =========================================================
# CONFIGURACIÓN GOOGLE SHEETS
# =========================================================
SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"

# 👉 PON AQUÍ LOS GID DE CADA PESTAÑA (UNA VEZ)
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

# =========================================================
# CARGA DE DATOS
# =========================================================
df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_exped = load_sheet("EXPEDIDORES")
df_trazas = load_sheet("TRAZAS_CONFIG")



# =========================================================
# APP
# =========================================================
st.title("Generador de etiquetas – Productos de la pesca")

# ---------------------------------------------------------
# IDENTIFICACIÓN COMERCIAL
# ---------------------------------------------------------
st.header("Identificación del producto")

nombre_base = st.selectbox(
    "Nombre base",
    df_productos["NOMBRE_BASE"].dropna().unique()
)

forma = st.selectbox(
    "Forma de transformación",
    df_transform.iloc[:, 0].dropna().unique()
)

estado = st.selectbox(
    "Estado del producto",
    df_estados.iloc[:, 0].dropna().unique()
)

estado = estado.lower().strip()


nombre_comercial = f"{nombre_base} {forma} {estado}"
st.success(f"Nombre comercial final: {nombre_comercial}")

# ---------------------------------------------------------
# DATOS TÉCNICOS (CAPADOS)
# ---------------------------------------------------------
producto = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]

st.header("Datos técnicos")

st.text_input(
    "Nombre científico",
    value=producto["NOMBRE_CIENTIFICO"],
    disabled=True
)

if pd.notna(producto["INGREDIENTES"]):
    st.text_input(
        "Ingredientes",
        value=producto["INGREDIENTES"],
        disabled=True
    )

# ---------------------------------------------------------
# ALÉRGENOS (AUTOMÁTICOS SEGÚN CONTIENE)
# ---------------------------------------------------------
def norm_upper(x):
    return str(x).strip().upper()

contiene = norm_upper(producto["ALERGENOS"])

# Asegurar columnas esperadas
cols = [c.strip().upper() for c in df_trazas.columns]
# Creamos un mapa por si vienen en minúsculas o con espacios
colmap = {c.strip().upper(): c for c in df_trazas.columns}

if "CONTIENE" not in cols or "PUEDE_CONTENER" not in cols:
    st.error("La hoja TRAZAS_CONFIG debe tener columnas: CONTIENE y PUEDE_CONTENER")
    st.stop()

col_contiene = colmap["CONTIENE"]
col_puede = colmap["PUEDE_CONTENER"]

df_trazas[col_contiene] = df_trazas[col_contiene].astype(str).str.strip().str.upper()
match = df_trazas[df_trazas[col_contiene] == contiene]

puede_contener = ""
if not match.empty:
    puede_contener = str(match.iloc[0][col_puede]).strip()

if puede_contener:
    texto_alergenos = f"Contiene {contiene}. Puede contener {puede_contener}."
else:
    texto_alergenos = f"Contiene {contiene}."

st.text_input("Alérgenos", value=texto_alergenos, disabled=True)



# ---------------------------------------------------------
# ORIGEN DEL LOTE
# ---------------------------------------------------------
st.header("Origen del lote")

metodo = st.selectbox(
    "Método de producción",
    df_metodo.iloc[:, 0].dropna().unique()
)

zona = arte = None

if metodo.lower().strip() == "capturado":

    zona = st.selectbox(
        "Zona de captura (FAO)",
        df_zonas.iloc[:, 0].dropna().unique()
    )
    arte = st.selectbox(
        "Arte de pesca",
        df_artes.iloc[:, 0].dropna().unique()
    )

# ---------------------------------------------------------
# FECHAS
# ---------------------------------------------------------
st.header("Fechas")

fecha_cad = st.date_input(
    "Fecha de caducidad",
    min_value=date.today()
)

fecha_cong = fecha_descong = None

if estado in ["congelado", "descongelado"]:
    fecha_cong = st.date_input("Fecha de congelación")

if estado == "descongelado":
    fecha_descong = st.date_input("Fecha de descongelación")

# ---------------------------------------------------------
# DATOS LEGALES (OBLIGATORIOS)
# ---------------------------------------------------------
st.header("Datos legales")

expedidor = st.selectbox(
    "Expedidor",
    df_exped["EXPEDIDOR"].dropna().unique()
)

ovalo = df_exped[df_exped["EXPEDIDOR"] == expedidor]["OVALO_SANITARIO"].iloc[0]
st.text_input("Óvalo sanitario", value=ovalo, disabled=True)

# ---------------------------------------------------------
# VALIDACIÓN FINAL
# ---------------------------------------------------------
st.divider()

if st.button("Generar etiqueta"):
    errores = []

    if metodo == "Capturado":
        if not zona:
            errores.append("Falta la zona de captura")
        if not arte:
            errores.append("Falta el arte de pesca")

    if estado == "congelado" and not fecha_cong:
        errores.append("Falta la fecha de congelación")

    if estado == "descongelado" and (not fecha_cong or not fecha_descong):
        errores.append("Faltan fechas de congelación o descongelación")

    if not expedidor or not ovalo:
        errores.append("Faltan datos de expedidor u óvalo sanitario")

    if errores:
        st.error(" | ".join(errores))
    else:
        st.success("Etiqueta validada correctamente")

        st.markdown("### 🏷️ Resumen de etiqueta")
        st.markdown(f"**Nombre comercial:** {nombre_comercial}")
        st.markdown(f"**Nombre científico:** {producto['NOMBRE_CIENTIFICO']}")
        if pd.notna(producto["INGREDIENTES"]):
            st.markdown(f"**Ingredientes:** {producto['INGREDIENTES']}")
        st.markdown(f"**Alérgenos:** {texto_alergenos}")
        st.markdown(f"**Método de producción:** {metodo}")
        if metodo == "Capturado":
            st.markdown(f"**Zona FAO:** {zona}")
            st.markdown(f"**Arte de pesca:** {arte}")
        st.markdown(f"**Estado:** {estado}")
        if fecha_cong:
            st.markdown(f"**Fecha congelación:** {fecha_cong}")
        if fecha_descong:
            st.markdown(f"**Fecha descongelación:** {fecha_descong}")
        st.markdown(f"**Fecha de caducidad:** {fecha_cad}")
        st.markdown(f"**Expedidor:** {expedidor}")
        st.markdown(f"**Óvalo sanitario:** {ovalo}")




