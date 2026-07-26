# 🔬 BioLichen - Analizador & Bioindicador Ambiental

**BioLichen** es una aplicación interactiva desarrollada en Python con **Streamlit** y **OpenCV** para la estimación de cobertura de líquenes en imágenes, procesamiento digital de muestras y cálculo del **Índice de Pureza Atmosférica (IPA)** para la bioindicación de la calidad del aire.

---

## 🌟 Características Principales

* 🖼️ **Procesamiento Digital de Imágenes:** 
  * Ajustes dinámicos de brillo y contraste en tiempo real.
  * Segmentación por espacios de color **HSV** para estimar el porcentaje exacto de cobertura del liquen.
  * Detección de textura y bordes mediante algoritmos de **Canny**.
* 📊 **Análisis Espectral (Histogramas):** Visualización de la distribución de frecuencias de los canales de color (RGB) para analizar pigmentación y clorofila.
* 🌍 **Bioindicación Ambiental (Índice IPA):** Cálculo automático del estado de contaminación del aire basado en el conteo de morfotipos observados (*Fruticulosos, Foliáceos y Crustáceos*).
* 📍 **Geolocalización Automática:** Extracción de coordenadas GPS a partir de los metadatos **EXIF** incrustados en las fotografías de campo y despliegue en mapa interactivo.
* 📄 **Exportación de Reportes:** Generación y descarga de resúmenes de datos en formato **CSV** e inspección en **JSON**.
* 🧪 **Modo de Pruebas:** Incluye muestras sintéticas generadas aleatoriamente (*Xanthoria parietina, Usnea barbata, Physcia aipolia*) para evaluar el software sin necesidad de cargar imágenes propias.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.8+
* **Interfaz Gráfica:** [Streamlit](https://streamlit.io/)
* **Visión por Computadora & Gráficos:** OpenCV (`opencv-python`), Matplotlib, Pillow (PIL)
* **Procesamiento de Datos:** Pandas, NumPy

---

## 🚀 Instalación y Ejecución Local

Sigue estos pasos para ejecutar la aplicación en tu máquina local:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/TU_USUARIO/TU_REPOSITORIO.git](https://github.com/TU_USUARIO/TU_REPOSITORIO.git)
cd TU_REPOSITORIO

### 2. También puedes ejecutarlo directamente del navegador en el siguiente enlace:

https://5n3pxkeemn3wuu4jnjqskq.streamlit.app/
