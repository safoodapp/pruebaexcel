import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF

# =========================================================
# 1. CONFIGURACIÓN Y CARGA (Añadido PAÍS_ORIGEN)
# =========================================================
SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {
    "PRODUCTOS": "0", "FORMAS_TRANSFORMACION": "1141842769", "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476", "ZONAS_FAO": "907306114", "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266", "TRAZAS_CONFIG": "1059656739",
    "PAIS_ORIGEN": "PON_AQUI_EL_GID_CUANDO_LO_TENGAS" # <--- Cambia esto luego
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
        # Si falla (como el de países que no tiene GID aún), devolvemos lista básica
        if name == "PAIS_ORIGEN":
            return pd.DataFrame({"PAIS": ["España", "Marruecos", "Portugal", "Islandia", "Noruega"]})
        return pd.DataFrame()

# Cargar dataframes
df_productos = load_sheet("PRODUCTOS")
df_transform = load_sheet("FORMAS_TRANSFORMACION")
df_estados = load_sheet("ESTADOS_PRODUCTO")
df_metodo = load_sheet("METODO_PRODUCCION")
df_zonas = load_sheet("ZONAS_FAO")
df_artes = load_sheet("ARTES_PESCA")
df_exped = load_sheet("EXPEDIDORES")
df_trazas_config = load_sheet("TRAZAS_CONFIG")
df_paises = load_sheet("PAIS_ORIGEN")

def preparar_lista(df, col_idx=0, col_name=None):
    if df.empty: return ["Selecciona una opción"]
    if col_name: items = df[col_name].dropna().unique().tolist()
    else: items = df.iloc[:, col_idx].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

# =========================================================
# 2. INTERFAZ (Añadido selector de País)
# =========================================================
st.title("🏷️ Generador de Etiquetas Inteligente")

c1, c2 = st.columns(2)
with c1: nombre_base = st.selectbox("Producto", preparar_lista(df_productos, col_name="NOMBRE_BASE"))
with c2: forma = st.selectbox("Transformación", preparar_lista(df_transform))

c3, c4, c5 = st.columns(3)
with c3: estado = st.selectbox("Estado", preparar_lista(df_estados))
with c4: metodo = st.selectbox("Producción", preparar_lista(df_metodo))
with c5: pais_origen = st.selectbox("País de Origen", preparar_lista(df_paises))

zona, arte = "N/A", "N/A"
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    c6, c7 = st.columns(2)
    with c6: zona = st.selectbox("Zona FAO", preparar_lista(df_zonas))
    with c7: arte = st.selectbox("Arte de Pesca", preparar_lista(df_artes))

lote = st.text_input("Número de Lote")
# ... (resto de inputs de fecha y cantidad iguales que tu código anterior) ...
fecha_cad = st.date_input("Fecha de Caducidad", value=date.today())
cantidad = st.number_input("Número de etiquetas", min_value=1, value=1)

# =========================================================
# 3. FUNCIÓN PDF SEGÚN TU BOCETO
# =========================================================
def generar_pdf_boceto(datos, cantidad):
    pdf = FPDF(orientation='P', unit='mm', format=(100, 150))
    pdf.set_auto_page_break(auto=False)
    
    for _ in range(int(cantidad)):
        pdf.add_page()
        mx = 5
        ancho_util = 100 - (mx * 2)

        # --- CABECERA DIVIDIDA ---
        # Parte Izquierda: Nombres
        pdf.set_xy(mx, 5)
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(55, 6, datos['nombre_base'].upper(), align='L')
        pdf.set_font("Arial", 'I', 9)
        pdf.set_x(mx)
        pdf.cell(55, 5, f"({datos['nombre_cientifico']})", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.set_x(mx)
        pdf.cell(55, 5, f"producto {datos['mencion_estado'].lower()}", ln=True) # MINÚSCULAS

        # Parte Derecha: Cuadro LOTE
        pdf.rect(65, 5, 30, 20)
        pdf.set_xy(65, 7)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(30, 5, "LOTE:", align='C', ln=True)
        pdf.set_font("Arial", 'B', 12)
        pdf.set_x(65)
        pdf.cell(30, 8, datos['lote'], align='C')

        # Línea divisoria
        pdf.line(mx, 30, 100-mx, 30)

        # --- INGREDIENTES DINÁMICOS ---
        curr_y = 35
        if datos['ingredientes']:
            pdf.set_xy(mx, curr_y)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(25, 5, "Ingredientes: ", ln=0)
            pdf.set_font("Arial", '', 8)
            pdf.multi_cell(ancho_util - 25, 4.5, datos['ingredientes'], align='J')
            curr_y = pdf.get_y() + 2

        # Alérgenos (Siempre salen)
        pdf.set_xy(mx, curr_y)
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(ancho_util, 5, f"CONTIENE: {str(datos['alergenos']).upper()}", align='L')
        
        # --- BLOQUE TRAZABILIDAD INTELIGENTE ---
        pdf.line(mx, 70, 100-mx, 70)
        pdf.set_xy(mx, 75)
        pdf.set_font("Arial", 'B', 9)
        
        # Solo si NO es acuicultura
        if "acuicultura" not in str(datos['metodo']).lower():
            pdf.cell(ancho_util, 6, f"ZONA DE CAPTURA: {datos['zona']}", ln=True, align='C')
            pdf.set_x(mx)
            pdf.cell(ancho_util, 6, f"ARTE DE PESCA: {datos['arte']}", ln=True, align='C')
        
        pdf.set_x(mx)
        pdf.cell(ancho_util, 6, f"MÉTODO DE PESCA: {datos['metodo']}", ln=True, align='C')
        pdf.set_x(mx)
        pdf.cell(ancho_util, 6, f"PAÍS DE ORIGEN: {datos['pais']}", ln=True, align='C')

        # --- BLOQUE CONSERVACIÓN ---
        pdf.line(mx, 105, 100-mx, 105)
        pdf.set_xy(mx, 110)
        pdf.set_font("Arial", 'B', 9)
        pdf.multi_cell(ancho_util, 5, datos['mencion_conservacion'], align='C')

        # --- FECHA CADUCIDAD ---
        pdf.line(mx, 130, 100-mx, 130)
        pdf.set_xy(mx, 132)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(ancho_util, 10, f"F. CAD: {datos['f_cad']}", align='C')

        # --- PIE DE PÁGINA ---
        pdf.set_xy(mx, 142)
        pdf.set_font("Arial", '', 7)
        pdf.multi_cell(60, 3, datos['expedidor_info'])
        
        # Óvalo
        pdf.ellipse(75, 140, 20, 8)
        pdf.set_xy(75, 141)
        pdf.set_font("Arial", 'B', 6)
        pdf.cell(20, 2, "ES", align='C', ln=True)
        pdf.set_x(75)
        pdf.cell(20, 2, datos['ovalo'], align='C')

    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# =========================================================
# 4. BOTÓN (Ajustado)
# =========================================================
if st.button("🚀 GENERAR ETIQUETAS"):
    if nombre_base != "Selecciona una opción" and lote:
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        
        # Lógica de conservación (resumida aquí para el ejemplo)
        mencion_cons = "CONSERVAR ENTRE 0-4ºC."
        if "CONGELADO" in estado.upper(): mencion_cons = "CONSERVAR A -18ºC."

        pdf_bytes = generar_pdf_boceto({
            "nombre_base": nombre_base,
            "nombre_cientifico": prod_row["NOMBRE_CIENTIFICO"],
            "mencion_estado": estado,
            "lote": lote,
            "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
            "alergenos": limpiar_nan(prod_row["ALERGENOS"]),
            "metodo": metodo,
            "zona": zona,
            "arte": arte,
            "pais": pais_origen,
            "mencion_conservacion": mencion_cons,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "expedidor_info": "PESCADOS SANTIAGO S.L. Madrid",
            "ovalo": "12.3456/M"
        }, cantidad)
        
        st.download_button("📥 DESCARGAR", pdf_bytes, "etiqueta.pdf")













































