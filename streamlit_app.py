import streamlit as st
import pandas as pd
from datetime import date, timedelta

# =========================================================
# 1. CONFIGURACIÓN Y CARGA DE DATOS
# =========================================================
st.set_page_config(page_title="Generador Santiago y Santiago", layout="wide")

st.markdown("""
    <style>
    .etiqueta-container {
        background-color: #eeeeee;
        padding: 20px;
        display: flex;
        justify-content: center;
    }
    @media print {
        body * { visibility: hidden; }
        .etiqueta-imprimir, .etiqueta-imprimir * { visibility: visible; }
        .etiqueta-imprimir { position: absolute; left: 0; top: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

SPREADSHEET_ID = "1gMEnVHqQmTqfhwMWmyybliH_ar4veAFq179FKpU6ZTA"
GIDS = {
    "PRODUCTOS": "0", "FORMAS_TRANSFORMACION": "1141842769", "ESTADOS_PRODUCTO": "57656075",
    "METODO_PRODUCCION": "1900442476", "ZONAS_FAO": "907306114", "ARTES_PESCA": "1510153858",
    "EXPEDIDORES": "1402611266", "TRAZAS_CONFIG": "1059656739",
    "PAIS_ORIGEN": "TU_GID_AQUI" 
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
    if df is None or df.empty: return ["Selecciona una opción"]
    items = df[col_name].dropna().unique().tolist() if col_name else df.iloc[:, 0].dropna().unique().tolist()
    return ["Selecciona una opción"] + items

# =========================================================
# 2. INTERFAZ DE USUARIO
# =========================================================
st.title("🏷️ Generador Pro Santiago y Santiago")

c1, c2 = st.columns(2)
with c1: nombre_base = st.selectbox("Producto", preparar_lista(df_productos, "NOMBRE_BASE"))
with c2: forma = st.selectbox("Transformación", preparar_lista(df_transform))

c3, c4, c5 = st.columns(3)
with c3: estado = st.selectbox("Estado (Fresco/Cong/Descong)", preparar_lista(df_estados))
with c4: metodo = st.selectbox("Producción", preparar_lista(df_metodo))
with c5: pais_orig = st.selectbox("País de Origen", ["España", "Marruecos", "Portugal", "Islandia", "Noruega"])

zona, arte = "N/A", "N/A"
if "acuicultura" not in str(metodo).lower() and metodo != "Selecciona una opción":
    c6, c7 = st.columns(2)
    with c6: zona = st.selectbox("Zona FAO", preparar_lista(df_zonas))
    with c7: arte = st.selectbox("Arte de Pesca", preparar_lista(df_artes))

lote = st.text_input("Número de Lote")

st.subheader("📅 Fechas")
fe1, fe2, fe3 = st.columns(3)
with fe1: f_elab = st.date_input("Fecha de Elaboración", value=date.today())
with fe2:
    fecha_descong = None
    if "DESCONGELADO" in str(estado).upper():
        fecha_descong = st.date_input("Fecha de Descongelación", value=date.today())
with fe3:
    default_cad = date.today() + timedelta(days=3) if fecha_descong else date.today() + timedelta(days=7)
    fecha_cad = st.date_input("Fecha de Caducidad", value=default_cad)

# =========================================================
# 3. EL MOLDE DINÁMICO (3 ETIQUETAS EN 1)
# =========================================================
def render_etiqueta_html(d):
    # --- LÓGICA DINÁMICA DE TEXTOS SEGÚN ESTADO ---
    if "DESCONGELADO" in d['estado'].upper():
        mencion_cons = "CONSERVAR ENTRE 0-4ºC. NO VOLVER A CONGELAR."
        texto_estado = "producto descongelado"
        bloque_descong = f"<p style='margin: 2px 0;'><strong>F. DESCONGELACIÓN:</strong> {d['f_des']}</p>"
    elif "CONGELADO" in d['estado'].upper():
        mencion_cons = "CONSERVAR A -18ºC. UNA VEZ DESCONGELADO NO VOLVER A CONGELAR."
        texto_estado = "producto congelado"
        bloque_descong = ""
    else: # FRESCO
        mencion_cons = "CONSERVAR ENTRE 0-4ºC. COCINAR ANTES DE CONSUMIR."
        texto_estado = "producto fresco"
        bloque_descong = ""

    return f"""
    <div class="etiqueta-imprimir" style="width: 380px; height: 600px; border: 1px solid #000; padding: 20px; font-family: Arial, sans-serif; background-color: white; color: black; position: relative;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <h2 style="margin: 0; font-size: 22px; text-transform: uppercase;">{d['nombre']}</h2>
                <i style="font-size: 13px;">({d['cientifico']})</i><br>
                <span style="font-size: 13px;">{d['forma'].lower()}</span>
            </div>
            <div style="border: 2px solid black; padding: 5px; text-align: center; min-width: 85px;">
                <small style="font-size: 10px;">LOTE:</small><br>
                <strong style="font-size: 18px;">{d['lote']}</strong>
            </div>
        </div>
        <hr style="border: 0; border-top: 1px solid black; margin: 10px 0;">
        <div style="font-size: 11px; line-height: 1.3;">
            <p style="margin: 3px 0;"><strong>INGREDIENTES:</strong> {d['ingredientes']}</p>
            <p style="margin: 3px 0;"><strong>CONTIENE:</strong> {d['alergenos']}</p>
        </div>
        <hr style="border: 0; border-top: 1px solid black; margin: 10px 0;">
        <div style="font-size: 11px; line-height: 1.3;">
            {"<p style='margin: 2px 0;'><strong>ZONA DE CAPTURA:</strong> " + d['zona'] + "</p>" if d['zona'] != "N/A" else ""}
            {"<p style='margin: 2px 0;'><strong>ARTE DE PESCA:</strong> " + d['arte'] + "</p>" if d['arte'] != "N/A" else ""}
            <p style="margin: 2px 0;"><strong>MÉTODO DE PESCA:</strong> {d['metodo']}</p>
            <p style="margin: 2px 0;"><strong>PAÍS DE ORIGEN:</strong> {d['pais']}</p>
        </div>
        <div style="text-align: center; margin-top: 15px; border: 1px solid black; padding: 5px;">
            <p style="font-weight: bold; margin: 0; font-size: 11px; text-transform: uppercase;">{mencion_cons}</p>
            <p style="font-size: 11px; margin: 2px 0;">{texto_estado}</p>
        </div>
        <div style="text-align: center; border-top: 1px solid black; margin-top: 15px; padding-top: 5px;">
            <p style="margin: 2px 0; font-size: 12px;"><strong>F. ELABORACIÓN:</strong> {d['f_el']}</p>
            {bloque_descong}
            <h2 style="margin: 5px 0; font-size: 20px;">F. CAD: {d['f_cad']}</h2>
        </div>
        <div style="position: absolute; bottom: 15px; width: 340px; display: flex; justify-content: space-between; align-items: flex-end;">
            <div style="font-size: 9px; line-height: 1.1;">
                <strong>{d['expedidor']}</strong><br>
                Calle Laguna del Marquesado 43C, 28021, Madrid
            </div>
            <div style="border: 1.5px solid black; border-radius: 50%; padding: 4px 8px; text-align: center; font-size: 9px; min-width: 60px;">
                ES<br><strong>{d['ovalo']}</strong>
            </div>
        </div>
    </div>
    """

# =========================================================
# 4. EJECUCIÓN
# =========================================================
if nombre_base != "Selecciona una opción" and lote:
    prod_row = df_productos[df_productos["NOMBRE_BASE"] == nombre_base].iloc[0]
    
    datos_finales = {
        "nombre": nombre_base,
        "cientifico": prod_row["NOMBRE_CIENTIFICO"],
        "forma": forma if forma != "Selecciona una opción" else "",
        "estado": estado,
        "lote": lote,
        "ingredientes": limpiar_nan(prod_row["INGREDIENTES"]),
        "alergenos": limpiar_nan(prod_row["ALERGENOS"]),
        "metodo": metodo,
        "zona": zona,
        "arte": arte,
        "pais": pais_orig,
        "f_el": f_elab.strftime("%d/%m/%Y"),
        "f_des": fecha_descong.strftime("%d/%m/%Y") if fecha_descong else None,
        "f_cad": fecha_cad.strftime("%d/%m/%Y"),
        "expedidor": "PESCADOS Y MARISCOS SANTIAGO S.L.",
        "ovalo": "12.14276/M"
    }

    st.markdown("### Previsualización")
    st.markdown('<div class="etiqueta-container">', unsafe_allow_html=True)
    st.markdown(render_etiqueta_html(datos_finales), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.button("🖨️ IMPRIMIR ETIQUETA", on_click=lambda: st.write("Consejo: Usa Ctrl+P y elige tu impresora de etiquetas"))
else:
    st.info("Configura los campos para generar la etiqueta.")















































