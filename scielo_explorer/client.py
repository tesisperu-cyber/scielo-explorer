from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import requests


class ArticleMetaError(RuntimeError):
    """Error controlado al consultar ArticleMeta."""


class ArticleMetaClient:
    """Cliente HTTP pequeño y conservador para endpoints ArticleMeta documentados."""

    def __init__(self, base_url: str, timeout: int = 25, user_agent: str | None = None):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent
                or "PYBOT-SciELO-Explorer/0.1 (research client; contact: configure-your-contact)",
                "Accept": "application/json, application/xml, text/xml, */*",
            }
        )

    def _url(self, endpoint: str) -> str:
        return urljoin(self.base_url, endpoint.lstrip("/"))

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response:
        url = self._url(endpoint)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ArticleMetaError(f"Error de conexión con ArticleMeta: {exc}") from exc

        if response.status_code == 429:
            raise ArticleMetaError(
                "HTTP 429: el servicio ha limitado temporalmente las solicitudes. "
                "Detén las consultas y vuelve a intentarlo más tarde; no se reintenta automáticamente."
            )
        if response.status_code in (401, 403):
            raise ArticleMetaError(
                f"HTTP {response.status_code}: acceso no autorizado o restringido. "
                "No se intenta eludir la restricción."
            )
        if not response.ok:
            excerpt = response.text[:500].replace("\n", " ")
            raise ArticleMetaError(
                f"HTTP {response.status_code} en {response.url}. Respuesta: {excerpt}"
            )
        return response

    def get_article_identifiers(self, issn: str, limit: int = 20) -> dict[str, Any]:
        """Obtiene identificadores asociados a un ISSN, si el endpoint acepta el filtro."""
        clean_issn = issn.strip()
        if not clean_issn:
            raise ArticleMetaError("Debes proporcionar un ISSN.")
        if not 1 <= int(limit) <= 100:
            raise ArticleMetaError("El límite debe estar entre 1 y 100 en esta interfaz.")
        response = self._get(
            "article/identifiers/",
            params={"issn": clean_issn, "limit": int(limit)},
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ArticleMetaError("ArticleMeta no devolvió JSON válido para los identificadores.") from exc
        if not isinstance(payload, dict):
            raise ArticleMetaError("La respuesta de identificadores no tiene la estructura JSON esperada.")
        return payload

    def get_article_metadata(self, code: str) -> dict[str, Any] | list[Any]:
        """Obtiene el registro JSON de un artículo mediante su código."""
        clean_code = code.strip()
        if not clean_code:
            raise ArticleMetaError("Debes proporcionar el código del artículo.")
        response = self._get("article/", params={"code": clean_code})
        try:
            return response.json()
        except ValueError as exc:
            raise ArticleMetaError(
                "La respuesta no es JSON. Comprueba que el código sea válido y que el endpoint devuelva metadatos."
            ) from exc

    def get_article_xml(self, code: str, xml_format: str = "xmlrsps") -> bytes:
        """Obtiene el XML individual con el formato admitido por dumparticles.py."""
        clean_code = code.strip()
        if not clean_code:
            raise ArticleMetaError("Debes proporcionar el código del artículo.")
        if xml_format not in {"xmlrsps", "xmlwos"}:
            raise ArticleMetaError("Formato XML no admitido. Usa xmlrsps o xmlwos.")
        response = self._get(
            "article",
            params={"code": clean_code, "format": xml_format},
        )
        content = response.content
        if not content:
            raise ArticleMetaError("ArticleMeta devolvió una respuesta vacía.")
        # Comprobación básica: evita guardar por error una página HTML como XML.
        prefix = content.lstrip()[:100].lower()
        if prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html"):
            raise ArticleMetaError("El servicio devolvió HTML en lugar de XML.")
        return content
