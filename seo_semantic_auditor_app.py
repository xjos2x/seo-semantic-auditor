import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

st.title("Auditor de Carga de Contenido")

uploaded_file = st.file_uploader(
    "Sube tu Excel o CSV",
    type=["csv", "xlsx"]
)

st.markdown("""
### 🚀 Reglas de Uso

📄 **Tipo de archivo permitido:** Excel `.xlsx` o CSV `.csv`

📌 **Columnas obligatorias:**
- `url`
- `keyword_enviada`

🔗 **La columna `url`** debe contener la URL completa a revisar

🎯 **La columna `keyword_enviada`** debe contener la keyword principal enviada a contenido

📦 **Tamaño máximo permitido:** 200 MB

🧩 **La herramienta analizará:**
- Title
- H1
- H2
- Meta Description
- Contenido SEO dentro de `contentSEO`
""")

def analyze_url(url):

    try:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://www.google.com/"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        status_code = response.status_code

        if status_code == 403:

            return {
                "status_code": status_code,
                "title": "",
                "h1": "403 ERROR",
                "h2": "",
                "meta_description": "",
                "contenido": "",
                "error": "Bloqueo 403 del servidor/CDN"
            }

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # TITLE
        title = soup.title.string if soup.title else ""

        # H1
        h1 = soup.find("h1")
        h1 = h1.get_text(" ", strip=True) if h1 else ""

        # H2
        h2_tags = soup.find_all("h2")

        h2_list = []

        for h2 in h2_tags:

            text = h2.get_text(
                " ",
                strip=True
            )

            if text:
                h2_list.append(text)

        h2_text = " | ".join(h2_list)

        # META DESCRIPTION
        meta = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        meta = (
            meta["content"]
            if meta and meta.get("content")
            else ""
        )

        # CONTENIDO SEO
        content_seo = soup.find(
            "div",
            id="contentSEO"
        )

        if content_seo:

            contenido = content_seo.get_text(
                " ",
                strip=True
            )

            contenido = " ".join(
                contenido.split()
            )

        else:

            contenido = ""

        return {
            "status_code": status_code,
            "title": title,
            "h1": h1,
            "h2": h2_text,
            "meta_description": meta,
            "contenido": contenido,
            "error": ""
        }

    except Exception as e:

        return {
            "status_code": "",
            "title": "",
            "h1": "",
            "h2": "",
            "meta_description": "",
            "contenido": "",
            "error": str(e)
        }

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):

        df = pd.read_csv(
            uploaded_file,
            sep=None,
            engine="python"
        )

    else:

        df = pd.read_excel(uploaded_file)

    # LIMPIEZA COLUMNAS
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    required_columns = [
        "url",
        "keyword_enviada"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        st.error(
            f"Faltan columnas: {missing_columns}"
        )

        st.stop()

    results = []

    progress_bar = st.progress(0)

    total_urls = len(df)

    for index, row in df.iterrows():

        url = str(
            row["url"]
        ).strip()

        keyword = str(
            row["keyword_enviada"]
        ).strip()

        data = analyze_url(url)

        result = {
            "url": url,
            "keyword_enviada": keyword,
            "status_code": data.get("status_code", ""),
            "title": data.get("title", ""),
            "h1": data.get("h1", ""),
            "h2": data.get("h2", ""),
            "meta_description": data.get(
                "meta_description",
                ""
            ),
            "contenido": data.get(
                "contenido",
                ""
            ),
            "error": data.get("error", "")
        }

        results.append(result)

        progress = (index + 1) / total_urls

        progress_bar.progress(progress)

        # PAUSA ENTRE REQUESTS
        time.sleep(1.5)

    result_df = pd.DataFrame(results)

    st.success(
        f"{len(result_df)} URLs analizadas"
    )

    st.dataframe(result_df)

    csv = result_df.to_csv(
        index=False
    )

    st.download_button(
        "Descargar CSV",
        csv,
        "resultado.csv",
        "text/csv"
    )
