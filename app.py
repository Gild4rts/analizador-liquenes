import streamlit as st
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from PIL.ExifTags import TAGS, GPSTAGS
import io
import json
from datetime import datetime

# =============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# =============================================================================
st.set_page_config(
    page_title="BioLichen - Analizador & Bioindicador Ambientales",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado ligero
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #2E7D32;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F1F8E9;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2E7D32;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. FUNCIONES DE APOYO Y GENERACIÓN DE MUESTRAS
# =============================================================================
@st.cache_data
def generate_sample_image(sample_type: str) -> Image.Image:
    """Genera imágenes de prueba sintéticas para probar la app inmediatamente."""
    width, height = 600, 400
    img = Image.new('RGB', (width, height), color=(80, 75, 70))
    draw = ImageDraw.Draw(img)
    
    np.random.seed(42)
    
    if sample_type == "Xanthoria parietina (Naranja / Foliáceo)":
        # Simular rocas con manchas anaranjadas/amarillas
        for _ in range(80):
            x = np.random.randint(50, width - 50)
            y = np.random.randint(50, height - 50)
            r = np.random.randint(15, 45)
            color = (
                np.random.randint(220, 255),
                np.random.randint(140, 190),
                np.random.randint(10, 40)
            )
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
            
    elif sample_type == "Usnea barbata (Verde / Fruticuloso)":
        # Simular líquenes ramificados verdosos
        for _ in range(120):
            x1 = np.random.randint(20, width - 20)
            y1 = np.random.randint(20, height - 20)
            x2 = x1 + np.random.randint(-40, 40)
            y2 = y1 + np.random.randint(-40, 40)
            color = (
                np.random.randint(100, 160),
                np.random.randint(170, 220),
                np.random.randint(70, 120)
            )
            draw.line([x1, y1, x2, y2], fill=color, width=np.random.randint(3, 8))
            
    else:  # Physcia aipolia (Grisáceo / Crustáceo)
        # Simular textura grisácea con pequeños puntos negros (apotecios)
        for _ in range(100):
            x = np.random.randint(30, width - 30)
            y = np.random.randint(30, height - 30)
            r = np.random.randint(10, 35)
            color = (
                np.random.randint(160, 200),
                np.random.randint(170, 210),
                np.random.randint(180, 215)
            )
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
            # Apotecios
            draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(30, 30, 30))

    return img


def convert_gps_coords(coords, ref):
    """Convierte coordenadas EXIF de formato DMS a Grados Decimales."""
    try:
        degrees = coords[0]
        minutes = coords[1]
        seconds = coords[2]
        
        # Convertir tuplas o fractions si existen
        deg = float(degrees[0]) / float(degrees[1]) if isinstance(degrees, tuple) else float(degrees)
        min_val = float(minutes[0]) / float(minutes[1]) if isinstance(minutes, tuple) else float(minutes)
        sec = float(seconds[0]) / float(seconds[1]) if isinstance(seconds, tuple) else float(seconds)
        
        decimal = deg + (min_val / 60.0) + (sec / 3600.0)
        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal
    except Exception:
        return None


def extract_exif_metadata(image: Image.Image):
    """Extrae metadatos de ubicación y fecha de la imagen."""
    exif_data = {}
    gps_coords = None
    
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == 'GPSInfo':
                    gps_data = {}
                    for g in value:
                        sub_tag = GPSTAGS.get(g, g)
                        gps_data[sub_tag] = value[g]
                    
                    if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                        lat = convert_gps_coords(gps_data['GPSLatitude'], gps_data.get('GPSLatitudeRef', 'N'))
                        lon = convert_gps_coords(gps_data['GPSLongitude'], gps_data.get('GPSLongitudeRef', 'E'))
                        if lat is not None and lon is not None:
                            gps_coords = (lat, lon)
                elif decoded in ['DateTimeOriginal', 'Make', 'Model']:
                    exif_data[decoded] = str(value)
    except Exception:
        pass
        
    return exif_data, gps_coords


# =============================================================================
# 3. INTERFAZ PRINCIPAL Y BARRA LATERAL
# =============================================================================
st.markdown('<div class="main-header">🔬 BioLichen: Analizador y Bioindicador Ambiental</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Procesamiento de imágenes, estimación de cobertura de líquenes e índice de pureza atmosférica.</div>', unsafe_allow_html=True)

st.sidebar.header("📁 Fuente de la Muestra")
source_option = st.sidebar.radio(
    "Selecciona cómo cargar la imagen:",
    ["Subir Archivo", "Muestras de Ejemplo"]
)

image_input = None

if source_option == "Subir Archivo":
    uploaded_file = st.sidebar.file_uploader("Carga una foto de liquen (JPG, PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image_input = Image.open(uploaded_file).convert('RGB')
else:
    sample_choice = st.sidebar.selectbox(
        "Elige una muestra predeterminada:",
        [
            "Xanthoria parietina (Naranja / Foliáceo)",
            "Usnea barbata (Verde / Fruticuloso)",
            "Physcia aipolia (Grisáceo / Crustáceo)"
        ]
    )
    image_input = generate_sample_image(sample_choice)

# Si no hay imagen cargada, mostrar mensaje de bienvenida y detener la ejecución limpia
if image_input is None:
    st.info("👈 Por favor, sube una imagen o selecciona una muestra de ejemplo en el menú lateral para comenzar el análisis.")
    st.stop()


# Convertir a arreglo NumPy para OpenCV
img_array = np.array(image_input)

# =============================================================================
# 4. PARÁMETROS DE PROCESAMIENTO EN SIDEBAR
# =============================================================================
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Ajustes de Procesamiento")

brightness = st.sidebar.slider("Ajuste de Brillo", -100, 100, 0)
contrast = st.sidebar.slider("Ajuste de Contraste", 0.5, 2.0, 1.0, 0.1)

mode = st.sidebar.selectbox(
    "Modo de Análisis Visual:",
    ["Segmentación de Cobertura (HSV)", "Detección de Textura (Canny)", "Imagen Ajustada"]
)

if mode == "Segmentación de Cobertura (HSV)":
    st.sidebar.subheader("Rango de Color del Liquen (HSV)")
    h_min = st.sidebar.slider("Hue Mínimo", 0, 179, 10)
    h_max = st.sidebar.slider("Hue Máximo", 0, 179, 85)
    s_min = st.sidebar.slider("Saturación Mínima", 0, 255, 40)
    v_min = st.sidebar.slider("Valor Mínimo (Brillo)", 0, 255, 40)

elif mode == "Detección de Textura (Canny)":
    st.sidebar.subheader("Umbrales Detección de Bordes")
    canny_thresh1 = st.sidebar.slider("Umbral Canny 1", 0, 255, 50)
    canny_thresh2 = st.sidebar.slider("Umbral Canny 2", 0, 255, 150)


# =============================================================================
# 5. PESTAÑAS DE TRABAJO EN LA INTERFAZ PRINCIPAL
# =============================================================================
tab_vision, tab_histo, tab_bio, tab_geo, tab_export = st.tabs([
    "🖼️ Visor y Procesamiento",
    "📊 Histograma de Color",
    "🌍 Bioindicación del Aire",
    "📍 Geolocalización",
    "📄 Exportar Reporte"
])

# -----------------------------------------------------------------------------
# TAB 1: VISOR Y PROCESAMIENTO DE IMAGEN
# -----------------------------------------------------------------------------
with tab_vision:
    # Aplicar ajuste de brillo y contraste con OpenCV
    adjusted_img = cv2.convertScaleAbs(img_array, alpha=contrast, beta=brightness)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Muestra Original")
        st.image(adjusted_img, use_container_width=True, caption="Imagen cargada con ajustes básicos")

    processed_img = adjusted_img.copy()
    coverage_percentage = 0.0
    
    with col2:
        st.subheader(f"Resultado: {mode}")
        
        if mode == "Segmentación de Cobertura (HSV)":
            hsv = cv2.cvtColor(adjusted_img, cv2.COLOR_RGB2HSV)
            lower_bound = np.array([h_min, s_min, v_min])
            upper_bound = np.array([h_max, 255, 255])
            
            mask = cv2.inRange(hsv, lower_bound, upper_bound)
            processed_img = cv2.bitwise_and(adjusted_img, adjusted_img, mask=mask)
            
            # Cálculo del Porcentaje de Cobertura
            total_pixels = mask.shape[0] * mask.shape[1]
            lichen_pixels = cv2.countNonZero(mask)
            coverage_percentage = (lichen_pixels / total_pixels) * 100
            
            st.image(processed_img, use_container_width=True, caption="Máscara de segmentación de área del liquen")
            
            # Métrica de Cobertura
            st.markdown(f"""
            <div class="metric-card">
                <h3>Cobertura Estimada: <b>{coverage_percentage:.2f}%</b></h3>
                <p>Porcentaje de la superficie cubierta por el liquen según el filtro de color configurado.</p>
            </div>
            """, unsafe_allow_html=True)
            
        elif mode == "Detección de Textura (Canny)":
            gray = cv2.cvtColor(adjusted_img, cv2.COLOR_RGB2GRAY)
            processed_img = cv2.Canny(gray, canny_thresh1, canny_thresh2)
            st.image(processed_img, use_container_width=True, caption="Bordes y detalles de textura del liquen")
            
        else:
            st.image(adjusted_img, use_container_width=True, caption="Imagen con Brillo y Contraste ajustados")


# -----------------------------------------------------------------------------
# TAB 2: HISTOGRAMA DE COLOR
# -----------------------------------------------------------------------------
with tab_histo:
    st.subheader("Distribución de Canales de Color (RGB)")
    st.write("El análisis espectral del color permite identificar el grado de pigmentación y clorofila presente en la muestra.")
    
    fig, ax = plt.subplots(figsize=(8, 3.5))
    colors = ('red', 'green', 'blue')
    for i, col in enumerate(colors):
        hist = cv2.calcHist([adjusted_img], [i], None, [256], [0, 256])
        ax.plot(hist, color=col, label=f"Canal {col.upper()}")
        ax.set_xlim([0, 256])
    
    ax.set_title("Histograma de Frecuencia de Píxeles")
    ax.set_xlabel("Intensidad de Píxel (0 - 255)")
    ax.set_ylabel("Cantidad de Píxeles")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)


# -----------------------------------------------------------------------------
# TAB 3: BIOINDICACIÓN DE CALIDAD DEL AIRE
# -----------------------------------------------------------------------------
with tab_bio:
    st.subheader("🌱 Índice de Pureza Atmosférica (IPA)")
    st.write("Los líquenes son altamente sensibles a la contaminación del aire ($SO_2$ y compuestos nitrogenados). Asigna los tipos observados para calcular el nivel de pureza del aire:")
    
    col_bio1, col_bio2 = st.columns([1, 1])
    
    with col_bio1:
        st.markdown("#### Conteo de Morfotipos Observados")
        fruticose_count = st.number_input("🌿 **Fruticulosos** (Muy sensibles - Aire Limpio)", min_value=0, max_value=20, value=2)
        foliose_count = st.number_input("🍃 **Foliáceos** (Sensibilidad media - Aire Moderado)", min_value=0, max_value=20, value=3)
        crustose_count = st.number_input("🪨 **Crustáceos** (Resistentes - Toleran contaminación)", min_value=0, max_value=20, value=1)
        
        # Fórmula de Índice de Pureza Atmosférica (IPA)
        ipa_score = (fruticose_count * 3.0) + (foliose_count * 2.0) + (crustose_count * 1.0)
        
    with col_bio2:
        st.markdown("#### Diagnóstico Ambiental")
        
        if ipa_score >= 12:
            quality = "🟢 Excelente / Aire Limpio"
            desc = "Alta presencia de líquenes fruticulosos. El entorno presenta muy bajos niveles de contaminación industrial o vehicular."
        elif ipa_score >= 6:
            quality = "🟡 Calidad Moderada"
            desc = "Presencia equilibrada de líquenes foliáceos y crustáceos. Nivel medio de pureza en el aire."
        else:
            quality = "🔴 Aire Contaminado / Alterado"
            desc = "Dominancia de líquenes crustáceos o ausencia de especies sensibles. Elevada presencia de contaminantes."
            
        st.metric(label="Índice IPA Calculado", value=f"{ipa_score:.1f} pts")
        st.subheader(f"Estado del Aire: {quality}")
        st.write(desc)


# -----------------------------------------------------------------------------
# TAB 4: GEOLOCALIZACIÓN Y METADATOS EXIF
# -----------------------------------------------------------------------------
with tab_geo:
    st.subheader("📍 Geolocalización del Hallazgo")
    
    exif_info, gps_coords = extract_exif_metadata(image_input)
    
    col_map1, col_map2 = st.columns([1, 1])
    
    with col_map1:
        st.markdown("#### Coordenadas de la Muestra")
        if gps_coords:
            lat, lon = gps_coords
            st.success(f"Coordenadas GPS extraídas de los metadatos EXIF:")
            st.write(f"**Latitud:** {lat:.6f}")
            st.write(f"**Longitud:** {lon:.6f}")
        else:
            st.warning("No se encontraron metadatos GPS incrustados en la foto. Puedes ingresar la ubicación manualmente:")
            lat = st.number_input("Latitud", value=-37.9575, format="%.6f")
            lon = st.number_input("Longitud", value=-72.4332, format="%.6f")
            
        map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        
    with col_map2:
        st.markdown("#### Mapa de Ubicación")
        st.map(map_df, zoom=12)


# -----------------------------------------------------------------------------
# TAB 5: EXPORTAR REPORTE
# -----------------------------------------------------------------------------
with tab_export:
    st.subheader("📄 Generación de Reportes del Análisis")
    st.write("Descarga los datos del análisis para anexar a tus informes de campo o investigación académica.")
    
    report_data = {
        "Fecha de Análisis": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Modo de Análisis": mode,
        "Cobertura Estimada (%)": round(coverage_percentage, 2) if mode == "Segmentación de Cobertura (HSV)" else "N/A",
        "Conteo Fruticulosos": fruticose_count,
        "Conteo Foliáceos": foliose_count,
        "Conteo Crustáceos": crustose_count,
        "Índice IPA": ipa_score,
        "Calidad del Aire": quality,
        "Latitud": lat,
        "Longitud": lon
    }
    
    st.json(report_data)
    
    # Generar CSV para descarga
    df_report = pd.DataFrame([report_data])
    csv_buffer = io.StringIO()
    df_report.to_csv(csv_buffer, index=False)
    
    st.download_button(
        label="📥 Descargar Reporte Completo (CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"reporte_liquenes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )