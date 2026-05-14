import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import subprocess
import sys
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

def normalize_url(url):
    url = str(url).strip()

    if not url or url.lower() == "nan":
        return ""

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    return url

def install_playwright_browser():
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True
        )
    except Exception:
        pass

def analyze_page(page, url):

    try:
        url = normalize_url(url)

        if not url:
            return {
                "status_code": "",
                "title": "",
                "h1": "",
                "h2": "",
                "meta_description": "",
                "contenido": "",
                "error": "URL vacía o inválida"
            }

        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=45000
        )

        time.sleep(2)

        status_code = response.status if response else ""

        html = page.content()

        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        h1 = soup.find("h1")
        h1 = h1.get_text(" ", strip=True) if h1 else ""

        h2_tags = soup.find_all("h2")
        h2_list = []

        for h2 in h2_tags:
            text = h2.get_text(" ", strip=True)
            if text:
                h2_list.append(text)

        h2_text = " | ".join(h2_list)

        meta = soup.find("meta", attrs={"name": "description"})

        meta_description = (
            meta["content"].strip()
            if meta and meta.get("content")
            else ""
        )

        content_seo = soup.find("div", id="contentSEO")

        if content_seo:
            contenido = content_seo.get_text(" ", strip=True)
            contenido = " ".join(contenido.split())
        else:
            contenido = ""

        error = ""

        if status_code == 403:
            error = "403 detectado incluso usando navegador real"

        if not contenido:
            error = error or "No se encontró div id='contentSEO'"

        return {
            "status_code": status_code,
            "title": title,
            "h1": h1,
            "h2": h2_text,
            "meta_description": meta_description,
            "contenido": contenido,
            "error": error
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

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    required_columns = ["url", "keyword_enviada"]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        st.error(f"Faltan columnas: {missing_columns}")
        st.stop()

    results = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    total_urls = len(df)

    try:
        with sync_playwright() as p:

            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                install_playwright_browser()
                browser = p.chromium.launch(headless=True)

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="es-CL",
                viewport={"width": 1440, "height": 1200}
            )

            page = context.new_page()

            for i, (_, row) in enumerate(df.iterrows(), start=1):

                url = normalize_url(row["url"])
                keyword = str(row["keyword_enviada"]).strip()

                status_text.write(f"Analizando {i}/{total_urls}: {url}")

                data = analyze_page(page, url)

                results.append({
                    "url": url,
                    "keyword_enviada": keyword,
                    "status_code": data.get("status_code", ""),
                    "title": data.get("title", ""),
                    "h1": data.get("h1", ""),
                    "h2": data.get("h2", ""),
                    "meta_description": data.get("meta_description", ""),
                    "contenido": data.get("contenido", ""),
                    "error": data.get("error", "")
                })

                progress_bar.progress(i / total_urls)

                time.sleep(1)

            browser.close()

    except Exception as e:
        st.error(f"Error general ejecutando Playwright: {e}")
        st.stop()

    result_df = pd.DataFrame(results)

    st.success(f"{len(result_df)} URLs analizadas")

    st.dataframe(result_df)

    csv = result_df.to_csv(index=False)

    st.download_button(
        "Descargar CSV",
        csv,
        "resultado.csv",
        "text/csv"
    )
