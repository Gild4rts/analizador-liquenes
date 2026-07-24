import streamlit as st
import cv2
import numpy as np
import pandas as pd
from PIL import Image

# 1. Configuración de la página
st.set_page_config(
    page_title="Analizador de Líquenes - Bioindicación Antártica", 
    layout="wide"
)

st.title("🔬 Analizador de Líquenes & Bioindicación Térmica")
st.write("Herramienta de análisis cuantitativo para imágenes microscópicas de líquenes antárticos.")

# 2. Panel lateral para controles
st.sidebar.header("🎛️ Parámetros de Análisis")

# Selector de tipo de tinción histológica
tipo_tincion = st.sidebar.selectbox(
    "Tipo de tinción microscópica",
    ["Magenta / Rosado (Corte histológico)", "Azul / Violeta", "Verde Natural (Líquen vivo)"]
)

sensibilidad = st.sidebar.slider("Sensibilidad de detección", 10, 100, 50)

st.sidebar.markdown("---")
st.sidebar.header("📏 Calibración de Escala")
micras_por_pixel = st.sidebar.number_input(
    "Relación de escala (µm por píxel)", 
    min_value=0.01, 
    max_value=100.0, 
    value=1.5, 
    step=0.1,
    help="Indica cuántos micrómetros equivale 1 píxel según tu microscopio."
)

st.sidebar.markdown("---")
mostrar_mascara = st.sidebar.checkbox("Mostrar máscara binaria", value=False)

# 3. Carga de archivo
archivo_imagen = st.file_uploader(
    "Selecciona una foto del líquen (JPG/PNG)", 
    type=["jpg", "jpeg", "png"]
)

if archivo_imagen is not None:
    # Convertir imagen cargada
    imagen_pil = Image.open(archivo_imagen)
    imagen_np = np.array(imagen_pil)
    
    # Asegurar formato OpenCV (BGR)
    if len(imagen_np.shape) == 3 and imagen_np.shape[2] == 4:
        imagen_np = cv2.cvtColor(imagen_np, cv2.COLOR_RGBA2BGR)
    else:
        imagen_np = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)

    # 4. Procesamiento de imagen en espacio HSV
    hsv = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2HSV)

    if tipo_tincion == "Magenta / Rosado (Corte histológico)":
        limite_inferior = np.array([130, max(10, 110 - sensibilidad), 40])
        limite_superior = np.array([175, 255, 255])
    elif tipo_tincion == "Azul / Violeta":
        limite_inferior = np.array([90, max(10, 110 - sensibilidad), 40])
        limite_superior = np.array([135, 255, 255])
    else:  # Verde Natural
        limite_inferior = np.array([25, max(10, 110 - sensibilidad), 20])
        limite_superior = np.array([85, 255, 255])

    # Crear máscara binaria
    mascara = cv2.inRange(hsv, limite_inferior, limite_superior)
    
    # Limpieza morfológica de ruido
    kernel = np.ones((5, 5), np.uint8)
    mascara_limpia = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
    mascara_limpia = cv2.morphologyEx(mascara_limpia, cv2.MORPH_CLOSE, kernel)

    # Detección de contornos
    contornos, _ = cv2.findContours(mascara_limpia, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    imagen_resultado = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2RGB)
    area_total_pixeles = 0
    ancho_maximo_px = 0
    
    for c in contornos:
        area = cv2.contourArea(c)
        if area > 100:
            area_total_pixeles += area
            cv2.drawContours(imagen_resultado, [c], -1, (255, 0, 0), 2)
            
            # Calcular ancho horizontal (para estimación de espesor)
            _, _, w, _ = cv2.boundingRect(c)
            if w > ancho_maximo_px:
                ancho_maximo_px = w

    # 5. Cálculos Matemáticos Avanzados
    # A. Área real en micrómetros cuadrados y milímetros cuadrados
    area_um2 = area_total_pixeles * (micras_por_pixel ** 2)
    area_mm2 = area_um2 / 1_000_000

    # B. Espesor medio estimado (µm)
    longitud_talo_um = ancho_maximo_px * micras_por_pixel
    espesor_promedio_um = (area_um2 / longitud_talo_um) if longitud_talo_um > 0 else 0

    # C. Análisis Cromatico (CIE L*a*b*) sobre el área segmentada
    lab = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2LAB)
    pixeles_tejido = lab[mascara_limpia > 0]
    
    if len(pixeles_tejido) > 0:
        l_prom = np.mean(pixeles_tejido[:, 0])
        a_prom = np.mean(pixeles_tejido[:, 1])
        b_prom = np.mean(pixeles_tejido[:, 2])
        saturacion_cromatica = np.sqrt(a_prom**2 + b_prom**2)
    else:
        l_prom = a_prom = b_prom = saturacion_cromatica = 0

    # 6. Visualización de Resultados
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📷 Muestra Microscópica")
        st.image(imagen_pil, use_container_width=True)

    with col2:
        st.subheader("🔍 Segmentación y Estructura")
        if mostrar_mascara:
            st.image(mascara_limpia, caption="Máscara Binaria", use_container_width=True)
        else:
            st.image(imagen_resultado, caption="Áreas e identificación de tejido", use_container_width=True)

    # 7. Despliegue de Métricas Biológicas
    st.markdown("---")
    st.subheader("📊 Resultados Biométricos y Térmicos")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    total_pixeles_img = imagen_np.shape[0] * imagen_np.shape[1]
    porcentaje_cobertura = (area_total_pixeles / total_pixeles_img) * 100

    col_m1.metric("Área Real", f"{area_mm2:.4f} mm²", f"{area_um2:,.0f} µm²")
    col_m2.metric("Cobertura de Tejido", f"{porcentaje_cobertura:.2f} %")
    col_m3.metric("Espesor Promedio", f"{espesor_promedio_um:.1f} µm")
    col_m4.metric("Índice Croma (C*)", f"{saturacion_cromatica:.2f}")

    # 8. Exportación de Informe
    st.markdown("---")
    st.subheader("💾 Exportar Análisis")

    datos_informe = {
        "Archivo": [archivo_imagen.name],
        "Tipo Tinción": [tipo_tincion],
        "Área (px)": [int(area_total_pixeles)],
        "Área (µm²)": [round(area_um2, 2)],
        "Área (mm²)": [round(area_mm2, 4)],
        "Espesor Estimado (µm)": [round(espesor_promedio_um, 2)],
        "Cobertura (%)": [round(porcentaje_cobertura, 2)],
        "Índice Croma (C*)": [round(saturacion_cromatica, 2)]
    }
    
    df_resultado = pd.DataFrame(datos_informe)
    st.dataframe(df_resultado, use_container_width=True)

    csv = df_resultado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte en CSV",
        data=csv,
        file_name=f"reporte_{archivo_imagen.name.split('.')[0]}.csv",
        mime="text/csv",
    )

    st.success("¡Análisis biométrico completado con éxito!")