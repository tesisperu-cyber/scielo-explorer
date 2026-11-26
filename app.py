from __future__ import annotations

import json
import re
import zipfile
from io import BytesIO
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from scielo_explorer.client import ArticleMetaClient, ArticleMetaError
from scielo_explorer.xml_tools import inspect_xml, xml_to_text

st.set_page_config(
    page_title="SciELO Explorer | PYBOT",
    page_icon="📚",
    layout="wide",
)

st.title("📚 SciELO Explorer")
st.caption("Cliente experimental de SciELO ArticleMeta · Proyecto PYBOT")

st.info(
    "Esta aplicación consulta servicios públicos de SciELO. No instala ni replica "
    "el servidor ArticleMeta. La búsqueda temática se abre en el buscador oficial; "
    "la recuperación estructurada se realiza mediante identificadores o ISSN."
)

with st.sidebar:
    st.header("Conexión")
    base_url = st.text_input(
        "URL de ArticleMeta",
        value="https://articlemeta.scielo.org/api/v1",
        help="Servicio público de metadatos de SciELO. Puedes cambiarlo si SciELO publica otro endpoint.",
    ).strip().rstrip("/")
    timeout = st.slider("Tiempo máximo por solicitud (segundos)", 5, 60, 25)
    st.divider()
    st.caption("La aplicación no ejecuta dumparticles.py ni descarga toda la red SciELO.")

client = ArticleMetaClient(base_url=base_url, timeout=timeout)

tab_search, tab_detail, tab_xml, tab_about = st.tabs(
    ["🔎 Buscar", "📄 Consultar artículo", "🧬 XML", "ℹ️ Alcance y ayuda"]
)

def show_api_error(exc: Exception) -> None:
    st.error(f"No se pudo completar la consulta: {exc}")
    st.caption(
        "Comprueba la conexión, el endpoint y la disponibilidad del servicio. "
        "La aplicación no intenta eludir bloqueos ni repetir solicitudes indefinidamente."
    )

def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value or "scielo")
    return value[:100] or "scielo"

with tab_search:
    st.subheader("Buscar y localizar registros")
    search_mode = st.radio(
        "Método de búsqueda",
        ["Búsqueda temática en SciELO", "Artículos de una revista (ISSN)", "Identificador de artículo (code)"],
        horizontal=False,
    )

    if search_mode == "Búsqueda temática en SciELO":
        query = st.text_input(
            "Tema o ecuación de búsqueda",
            placeholder='"organizational citizenship behavior" OR "comportamiento ciudadano organizacional"',
        )
        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox(
                "Interfaz del buscador",
                ["all", "en", "es", "pt"],
                format_func=lambda x: {"all": "Sin preferencia", "en": "Inglés", "es": "Español", "pt": "Portugués"}[x],
            )
        with col2:
            count = st.number_input("Resultados solicitados en el buscador", 10, 1000, 100, 10)
        if query:
            params = f"q={quote_plus(query)}&count={int(count)}&output=site"
            if language != "all":
                params += f"&lang={language}"
            search_url = f"https://search.scielo.org/?{params}"
            st.markdown(f"[Abrir esta búsqueda en SciELO]({search_url})")
            st.caption(
                "La búsqueda temática se deriva al buscador oficial. Esta versión no extrae "
                "ni automatiza el HTML de resultados: para recuperar registros estructurados, "
                "usa el ISSN de la revista o el código del artículo."
            )
            st.code(search_url, language="text")

    elif search_mode == "Artículos de una revista (ISSN)":
        issn = st.text_input("ISSN de la revista", placeholder="0104-...")
        limit = st.number_input("Máximo de identificadores", min_value=1, max_value=100, value=20, step=5)
        if st.button("Consultar identificadores", type="primary", disabled=not issn.strip()):
            with st.spinner("Consultando ArticleMeta..."):
                try:
                    data = client.get_article_identifiers(issn=issn.strip(), limit=int(limit))
                    objects = data.get("objects", []) if isinstance(data, dict) else []
                    st.session_state["last_identifiers"] = objects
                    st.session_state["last_identifier_query"] = issn.strip()
                    st.success(f"ArticleMeta devolvió {len(objects)} identificadores.")
                    if not objects:
                        st.warning("No se recibieron identificadores. Comprueba el ISSN o la respuesta del servicio.")
                except ArticleMetaError as exc:
                    show_api_error(exc)

        objects = st.session_state.get("last_identifiers", [])
        if objects:
            df = pd.DataFrame(objects)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                "Descargar identificadores CSV",
                df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"scielo_identificadores_{safe_filename(st.session_state.get('last_identifier_query','issn'))}.csv",
                mime="text/csv",
            )
            codes = [str(x.get("code", "")) for x in objects if x.get("code")]
            selected_code = st.selectbox("Seleccionar código para consultar", codes)
            if st.button("Abrir artículo seleccionado"):
                st.session_state["selected_code"] = selected_code
                st.toast(f"Código seleccionado: {selected_code}")

    else:
        code = st.text_input("Código del artículo", placeholder="Código exacto devuelto por SciELO")
        if st.button("Consultar código", type="primary", disabled=not code.strip()):
            st.session_state["selected_code"] = code.strip()
            st.success("Código preparado. Abre la pestaña «Consultar artículo».")

with tab_detail:
    st.subheader("Consultar metadatos de un artículo")
    default_code = st.session_state.get("selected_code", "")
    article_code = st.text_input("Código (code)", value=default_code, key="article_code_input")
    if st.button("Recuperar metadatos", type="primary", disabled=not article_code.strip()):
        with st.spinner("Consultando metadatos..."):
            try:
                metadata = client.get_article_metadata(article_code.strip())
                st.session_state["article_metadata"] = metadata
                st.session_state["article_code"] = article_code.strip()
                st.success("Respuesta recibida desde ArticleMeta.")
            except ArticleMetaError as exc:
                show_api_error(exc)

    metadata = st.session_state.get("article_metadata")
    if metadata is not None:
        st.markdown("#### Respuesta original")
        st.json(metadata, expanded=False)
        st.download_button(
            "Descargar metadatos JSON",
            json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"{safe_filename(st.session_state.get('article_code','article'))}_metadata.json",
            mime="application/json",
        )

with tab_xml:
    st.subheader("Recuperar e inspeccionar XML")
    xml_code = st.text_input(
        "Código del artículo para recuperar XML",
        value=st.session_state.get("article_code", st.session_state.get("selected_code", "")),
        key="xml_code_input",
    )
    xml_format = st.selectbox(
        "Formato XML de ArticleMeta",
        ["xmlrsps", "xmlwos"],
        help="Son los dos formatos admitidos por el dumparticles.py original. Verifica el contenido de cada respuesta.",
    )
    if st.button("Descargar XML de este artículo", type="primary", disabled=not xml_code.strip()):
        with st.spinner(f"Solicitando {xml_format}..."):
            try:
                xml_bytes = client.get_article_xml(xml_code.strip(), xml_format=xml_format)
                st.session_state["article_xml_bytes"] = xml_bytes
                st.session_state["article_xml_code"] = xml_code.strip()
                st.session_state["article_xml_format"] = xml_format
                st.success(f"XML recibido: {len(xml_bytes):,} bytes.")
            except ArticleMetaError as exc:
                show_api_error(exc)

    xml_bytes = st.session_state.get("article_xml_bytes")
    if xml_bytes:
        report = inspect_xml(xml_bytes)
        c1, c2, c3 = st.columns(3)
        c1.metric("Tamaño", f"{len(xml_bytes):,} bytes")
        c2.metric("Secciones detectadas", report.get("section_count", 0))
        c3.metric("Referencias detectadas", report.get("reference_count", 0))
        st.write("**Diagnóstico estructural**")
        st.json(report, expanded=True)
        st.download_button(
            "Descargar XML original",
            data=xml_bytes,
            file_name=f"{safe_filename(st.session_state.get('article_xml_code','article'))}_{xml_format}.xml",
            mime="application/xml",
        )
        with st.expander("Vista previa del XML"):
            st.code(xml_bytes.decode("utf-8", errors="replace")[:30000], language="xml")
        with st.expander("Texto legible extraído (orientativo)"):
            st.text_area("Texto XML", xml_to_text(xml_bytes)[:30000], height=350)

with tab_about:
    st.subheader("Qué hace y qué no hace esta versión")
    st.markdown(
        """
        **Incluye**
        - Acceso al buscador temático oficial de SciELO mediante enlace.
        - Consulta de identificadores por ISSN en ArticleMeta.
        - Consulta de metadatos por código de artículo.
        - Solicitud individual de XML en `xmlrsps` o `xmlwos`.
        - Inspección básica del XML, vista previa y exportación.

        **No incluye todavía**
        - Descarga masiva de toda la red SciELO.
        - Extracción automatizada del HTML del buscador.
        - Traducción automática de títulos o resúmenes.
        - Garantía de texto completo: el contenido depende del registro y del formato devuelto.
        - Integración con la base SQLite de inventario de PYBOT.

        **Uso responsable**
        - Las consultas están acotadas y se realizan bajo demanda.
        - No se intenta eludir controles de acceso ni protecciones del servicio.
        - Si aparece un error HTTP o un bloqueo, detén la prueba y registra la respuesta.
        - Revisa las condiciones y licencias de cada revista antes de reutilizar o redistribuir textos.
        """
    )
    st.markdown(
        "[Documentación oficial ArticleMeta](https://github.com/scieloorg/articles_meta) · "
        "[Código original dumparticles.py](https://github.com/scieloorg/articles_meta/blob/master/processing/dumparticles.py) · "
        "[Buscador SciELO](https://search.scielo.org/)"
    )
    st.warning(
        "La documentación oficial de ArticleMeta indica que su API entrega registros bibliográficos "
        "en JSON y recomienda los archivos masivos mensuales para cargas iniciales. "
        "La descarga individual de toda la red por HTTP puede tardar varios días."
    )

st.divider()
st.caption("SciELO Explorer · Prototipo cliente independiente · No afiliado oficialmente a SciELO.")
