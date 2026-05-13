import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.title("Auditor SEO Semántico")

uploaded_file = st.file_uploader(
    "Sube tu Excel o CSV",
    type=["csv", "xlsx"]
)

def analyze_url(url):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

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

            text = h2.get_text(" ", strip=True)

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
            "title": title,
            "h1": h1,
            "h2": h2_text,
            "meta_description": meta,
            "contenido": contenido,
            "error": ""
        }

    except Exception as e:

        return {
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

    # Limpieza columnas
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    st.write(
        "Columnas detectadas:",
        list(df.columns)
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

    for _, row in df.iterrows():

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
