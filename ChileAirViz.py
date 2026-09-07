import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Config de la pagina
st.set_page_config(page_title="Análisis de Aeronaves - Chile", layout="wide")

# Añadi una imagen de fondo por estetica
def set_bg_url(url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{url}");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Aqui se llama a la funcion al inicio del script anterior
set_bg_url("https://images.unsplash.com/photo-1763309631391-3192b0ba0eb4?q=80&w=1283&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")

# Se añadio el logo de la univcersidad
col_logo, col_titulo = st.columns([1, 6])

with col_logo:
    st.image("https://cdn.uss.cl/content/uploads/2025/10/22175624/USShorizontal-tagline-ilumina-dark.svg", width=240)
    
with col_titulo:
    st.title("Análisis de Aeronaves Inscritas en Chile al 31 de Agosto 2026")
    st.caption("Datos obtenidos desde la API de datos.gob.cl")

# Funcion para consultar la API REST

@st.cache_data
def obtener_datos_api(limit_count):
    url = "https://datos.gob.cl/api/3/action/datastore_search"
    
    params = {
        "resource_id": "bef3f397-7832-46fd-9f55-ad959744fea1",
        "limit": limit_count
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                records = data["result"]["records"]
                return pd.DataFrame(records)
            else:
                st.error("La API respondió pero no se pudo procesar la consulta.")
                return pd.DataFrame()
        else:
            st.error(f"Error al conectar con la API. Codigo: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# Cargar y procesar datos

df = obtener_datos_api(2032)

if not df.empty:
    st.success(f"Los datos se cargaron correctamente, mostrando {len(df)} registros.")
    
    # Identificar la columna de matricula
    col_matricula = next((col for col in df.columns if 'MAT' in col.upper()), None)

    # Metricas destacadas
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Total Registros Cargados", len(df))
    with col_m2:
        if col_matricula:
            st.metric("Aeronaves Únicas", df[col_matricula].nunique())
        else:
            st.metric("Total Columnas", len(df.columns))
    with col_m3:
        if col_matricula:
            conteo_mat = df[col_matricula].value_counts()
            mats_copropiedad = conteo_mat[conteo_mat > 1].index
            st.metric("Aeronaves en Co-propiedad", len(mats_copropiedad))
        else:
            st.metric("Estado Servicio", "En linea")
        
    st.divider()

    # Primera tabla 
    st.subheader("Exploración de la Tabla Completa de Datos")
    st.dataframe(df, use_container_width=True, height=280)

    st.divider()

    # Busqueda individual usando el ID o la Matricula
    st.subheader("Consulta Detallada por Registro (ID o Matricula)")
    
    criterio_busqueda = st.radio(
        "Selecciona el criterio de búsqueda:",
        options=["Buscar por ID", "Buscar por Matricula"],
        horizontal=True
    )

    registro_filtrado = pd.DataFrame()

    if criterio_busqueda == "Buscar por ID":
        if '_id' in df.columns:
            id_opciones = sorted(df['_id'].tolist())
            id_seleccionado = st.selectbox(
                "Selecciona o escribe el ID del registro:",
                options=id_opciones
            )
            if id_seleccionado:
                registro_filtrado = df[df['_id'] == id_seleccionado]
        else:
            st.warning("La columna ID no está disponible.")

    else:  # Config para busqueda por matricula
        if col_matricula:
            mat_opciones = sorted(df[col_matricula].dropna().unique().tolist())
            mat_seleccionada = st.selectbox(
                f"Selecciona o escribe la matricula (columna '{col_matricula}'):",
                options=mat_opciones
            )
            if mat_seleccionada:
                registro_filtrado = df[df[col_matricula] == mat_seleccionada]
        else:
            st.warning("No se identificó una columna de matricula en la base de datos.")

    if not registro_filtrado.empty:
        st.write(f"**Registros encontrados:** {len(registro_filtrado)}")
        st.dataframe(registro_filtrado, use_container_width=True)
        
        st.caption("**Ficha de Datos Detallada:**")
        
        for idx, row in registro_filtrado.iterrows():
            if len(registro_filtrado) > 1:
                st.markdown(f"** Registro ID:** `{row.get('_id', idx)}`")
            
            col_f1, col_f2 = st.columns(2)
            datos_dict = row.to_dict()
            items = list(datos_dict.items())
            mitad = len(items) // 2
            
            with col_f1:
                for clave, valor in items[:mitad]:
                    st.write(f"**{clave}:** {valor}")
            with col_f2:
                for clave, valor in items[mitad:]:
                    st.write(f"**{clave}:** {valor}")
            
            if len(registro_filtrado) > 1:
                st.divider()

    st.divider()

    # Lista de aeronaves con mas de un propietario
    # aqui suponemos que son copropietarios ya que la misma matricula tiene mas de un operador
    st.subheader("Registro de Aeronaves en Co-propiedad")
    
    if col_matricula:
        df_copropiedad = df[df[col_matricula].isin(mats_copropiedad)].sort_values(by=col_matricula)
        
        if not df_copropiedad.empty:
            st.caption(f"Se muestran unicamente los registros de las **{len(mats_copropiedad)} matriculas** que poseen dos o más inscripciones/propietarios registrados.")
            st.dataframe(df_copropiedad, use_container_width=True, height=280)
        else:
            st.info("No se encontraron matriculas en co-propiedad en la muestra actual.")
    else:
        st.warning("No se identificó la columna de matricula en la base de datos.")

    st.divider()

    # Analisis grafico // todo lo relacionado a la tabla (exclui valores despreciables)
    st.subheader("Grafico de analisis y comparacion.")
    
    columnas_excluidas = ['_id', 'Ndeg', 'MATRICULA', col_matricula]
    columnas_disponibles = [col for col in df.columns if col not in columnas_excluidas and col is not None]
    
    col_opt1, col_opt2 = st.columns([2, 1])
    with col_opt1:
        columna_seleccionada = st.selectbox(
            "Selecciona la columna a comparar (Marca, Modelo, Estado, etc.):", 
            options=columnas_disponibles
        )
    with col_opt2:
        top_n = st.slider(
            "Cantidad de datos a mostrar:",
            min_value=5,
            max_value=50,
            value=15,
            step=5,
            help="Ajusta la cantidad de datos que muestra la tabla."
        )

    if columna_seleccionada:
        # calcula las frecuencias (veces que se repite un valor)
        conteo = df[columna_seleccionada].value_counts().head(top_n)
        
        if not conteo.empty:
            # Hace un sorting para que el valor mas grande quede arriba
            conteo_sorted = conteo.sort_values(ascending=True)
            
            # Ajuste de altura de la tabla
            altura_grafico = max(4, len(conteo_sorted) * 0.35)
            
            fig, ax = plt.subplots(figsize=(10, altura_grafico))
            
            # Barras horizontales
            bars = ax.barh(conteo_sorted.index.astype(str), conteo_sorted.values, color="#2E2D2D", edgecolor="black", linewidth=0.5)
            
            # Anotaciones de numero en el grafico // sin decimales 
            for bar in bars:
                width = bar.get_width()
                ax.text(width + (max(conteo_sorted.values) * 0.01), 
                        bar.get_y() + bar.get_height()/2, 
                        f'{int(width)}', 
                        va='center', ha='left', fontsize=8, fontweight='bold', color='#1E293B')

            ax.set_title(f"Muestra de {len(conteo_sorted)} datos para '{columna_seleccionada}'", fontsize=11, fontweight="bold", pad=12)
            ax.set_xlabel("Cantidad", fontsize=9, fontweight="bold")
            ax.tick_params(axis='both', labelsize=8.5)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.tight_layout()
            
            st.pyplot(fig)

            # Tabla con despliegue // muestra todos los datos sin limitar por el slider
            with st.expander(f"Tabla con datos de cantidades para '{columna_seleccionada}'"):
                conteo_completo = df[columna_seleccionada].value_counts()
                df_resumen = conteo_completo.reset_index()
                df_resumen.columns = [columna_seleccionada, "Cantidad"]
                df_resumen["Porcentaje del Total"] = (df_resumen["Cantidad"] / len(df) * 100).round(2).astype(str) + " %"
                st.dataframe(df_resumen, use_container_width=True)
        else:
            st.info("No hay datos disponibles en la columna seleccionada.")

else:
    st.warning("No se pudieron cargar datos desde la API.")
