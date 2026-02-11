import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF

# =========================================================
# 1. CONFIGURACIÓN Y ESTADO DE SESIÓN
# =========================================================
st.set_page_config(page_title="Generador de Etiquetas de Santiago y Santiago", layout="wide")

# Función para limpiar el estado y resetear campos
def reset_campos():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

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
    "EXPEDIDORES": "1402611266", "TRAZAS_CONFIG": "1059656739",
}

@st.cache_data(ttl=600)
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
# 3. INTERFAZ DE USUARIO (ORDEN SOLICITADO)
# =========================================================
st.title("🏷️ Generador de Etiquetas de Santiago y Santiago")

with st.sidebar:
    st.header("Menú")
    st.button("🔄 NUEVA ETIQUETA (Limpiar todo)", on_click=reset_campos)

# FILA 1: Producto y Transformación
col1, col2 = st.columns(2)
with col1:
    nombre_base = st.selectbox("Producto", preparar_lista(df_productos, col_name="NOMBRE_BASE"), key="prod")
with col2:
    forma = st.selectbox("Transformación", preparar_lista(df_transform, col_idx=0), key="trans")

# FILA 2: Estado y Producción
col3, col4 = st.columns(2)
with col3:
    estado = st.selectbox("Estado", preparar_lista(df_estados, col_idx=0), key="est")
with col4:
    metodo = st.selectbox("Producción", preparar_lista(df_metodo, col_idx=0), key="met")

# FILA 3: Zona FAO y Arte (Solo si es capturado/no acuicultura)
zona, arte = None, None
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    col5, col6 = st.columns(2)
    with col5:
        zona = st.selectbox("Zona FAO", preparar_lista(df_zonas, col_idx=0), key="z_fao")
    with col6:
        arte = st.selectbox("Arte de Pesca", preparar_lista(df_artes, col_idx=0), key="a_pesca")

# FILA 4: Lote (En medio)
lote = st.text_input("Número de Lote", key="lote_val")

# FILA 5: Fechas
col7, col8 = st.columns(2)
fecha_descong = None
with col7:
    if "DESCONGELADO" in str(estado).upper():
        fecha_descong = st.date_input("Fecha de Descongelación", value=date.today(), key="f_des")
with col8:
    # Lógica automática +3 días para descongelado
    default_cad = date.today()
    if "DESCONGELADO" in str(estado).upper() and fecha_descong:
        default_cad = fecha_descong + timedelta(days=3)
    fecha_cad = st.date_input("Fecha de Caducidad", value=default_cad, key="f_cad")

cantidad = st.number_input("Número de etiquetas a imprimir", min_value=1, value=1, key="cant")

# =========================================================
# 4. FUNCIÓN PDF (ETIQUETA COMPACTA Y AJUSTE DE TEXTO)
# =========================================================
def generar_pdf_a4(datos, cantidad):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=5)
    pdf.add_page()
    
    ancho_et, alto_et = 95, 95
    mx, my, sep = 7, 7, 5 
    curr_x, curr_y = mx, my

    for i in range(int(cantidad)):
        pdf.rect(curr_x, curr_y, ancho_et, alto_et)
        
        # Denominación Comercial
        pdf.set_xy(curr_x, curr_y + 4)
        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(ancho_et, 5, f"{datos['nombre_base'].upper()}\nPRODUCTO {datos['mencion_estado'].upper()}", align='C')
        
        # Nombre Científico
        pdf.set_font("Arial", 'I', 9)
        pdf.set_xy(curr_x, curr_y + 15)
        pdf.cell(ancho_et, 4, f"({datos['nombre_cientifico']})", align='C')

        # INGREDIENTES CON AJUSTE AUTOMÁTICO DE TAMAÑO
        pdf.line(curr_x, curr_y + 20, curr_x + ancho_et, curr_y + 20)
        if datos['ingredientes']:
            pdf.set_xy(curr_x + 2, curr_y + 21)
            # Si el texto es muy largo, reducimos la fuente para que quepa en el bloque
            longitud = len(datos['ingredientes'])
            f_size = 7 if longitud < 130 else (6 if longitud < 200 else 5)
            pdf.set_font("Arial", 'B', f_size)
            pdf.write(3, "INGREDIENTES: ")
            pdf.set_font("Arial", '', f_size)
            pdf.write(3, datos['ingredientes'])
        
        # CONTIENE (Alergenos)
        pdf.set_xy(curr_x + 2, curr_y + 34)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(ancho_et, 4, f"CONTIENE: {str(datos['alergenos']).upper()}")

        # SECCIÓN PESCA (Compacta y Negritas)
        pdf.rect(curr_x, curr_y + 43, ancho_et, 15)
        pdf.set_font("Arial", 'B', 8)
        pdf.set_xy(curr_x + 3, curr_y + 44)
        pdf.write(4, "ZONA DE CAPTURA: "); pdf.set_font("Arial", '', 8); pdf.write(4, f"{datos['zona'] if datos['zona'] else 'N/A'}")
        pdf.set_xy(curr_x + 3, curr_y + 48)
        pdf.set_font("Arial", 'B', 8); pdf.write(4, "MÉTODO DE PESCA: "); pdf.set_font("Arial", '', 8); pdf.write(4, f"{datos['metodo']}")
        pdf.set_xy(curr_x + 3, curr_y + 52)
        pdf.set_font("Arial", 'B', 8); pdf.write(4, "ARTE DE PESCA: "); pdf.set_font("Arial", '', 8); pdf.write(4, f"{datos['arte'] if datos['arte'] else 'N/A'}")

        # CONSERVACIÓN
        pdf.rect(curr_x, curr_y + 59, ancho_et, 8)
        pdf.set_xy(curr_x + 2, curr_y + 60)
        pdf.set_font("Arial", 'B', 7)
        pdf.multi_cell(ancho_et - 4, 3, datos['mencion_conservacion'].upper(), align='C')

        # TRAZABILIDAD (LOTE Y FECHAS XL)
        pdf.rect(curr_x, curr_y + 68, ancho_et, 14)
        pdf.set_xy(curr_x + 3, curr_y + 69)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 5, f"LOTE: {datos['lote']}")
        pdf.set_xy(curr_x + 3, curr_y + 75)
        pdf.set_font("Arial", 'B', 10)
        f_desc_txt = f"  DESCONG: {datos['f_descong']}" if datos['f_descong'] else ""
        pdf.cell(0, 5, f"CAD: {datos['f_cad']}{f_desc_txt}")

        # PIE DE PÁGINA (Empresa y Óvalo)
        pdf.set_xy(curr_x + 2, curr_y + 83)
        pdf.set_font("Arial", '', 7)
        pdf.multi_cell(ancho_et - 25, 3, f"{datos['expedidor']}\n28021 Madrid")
        
        pdf.ellipse(curr_x + 72, curr_y + 83, 18, 10)
        pdf.set_xy(curr_x + 72, curr_y + 84)
        pdf.set_font("Arial", 'B', 6); pdf.cell(18, 2.5, "ES", align='C', ln=True)
        pdf.set_x(curr_x + 72); pdf.cell(18, 2.5, str(datos['ovalo']), align='C', ln=True)
        pdf.set_x(curr_x + 72); pdf.cell(18, 2.5, "CE", align='C')

        # Posicionamiento de la siguiente etiqueta
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
# 5. EJECUCIÓN
# =========================================================
if st.button("🚀 GENERAR ETIQUETAS"):
    if nombre_base == "Selecciona una opción" or not lote:
        st.error("⚠️ Debes seleccionar un Producto e introducir un Lote.")
    else:
        prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
        
        info_etiqueta = {
            "nombre_base": f"{nombre_base} {forma if forma != 'Selecciona una opción' else ''}",
            "mencion_estado": estado,
            "nombre_cientifico": prod_row["NOMBRE_CIENTIFICO"],
            "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
            "alergenos": limpiar_nan(prod_row["ALERGENOS"]),
            "mencion_conservacion": "CONSERVAR ENTRE 0 Y 4ºC" if "DESCONGELADO" not in estado.upper() else "PRODUCTO DESCONGELADO. NO VOLVER A CONGELAR.",
            "metodo": metodo, "lote": lote, "zona": zona, "arte": arte,
            "f_cad": fecha_cad.strftime("%d/%m/%Y"),
            "f_descong": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
            "expedidor": df_exped.iloc[0]["EXPEDIDOR"],
            "ovalo": df_exped.iloc[0]["OVALO_SANITARIO"]
        }

        pdf_bytes = generar_pdf_a4(info_etiqueta, cantidad)
        st.success("✅ Etiquetas generadas correctamente.")
        st.download_button("📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"etiqueta_{lote}.pdf", mime="application/pdf")




