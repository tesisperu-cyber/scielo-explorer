from __future__ import annotations

from collections import Counter
from io import BytesIO

from lxml import etree


def _local_name(tag: str) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].lower()


def inspect_xml(xml_bytes: bytes) -> dict:
    """Inspección estructural no destructiva del XML recibido."""
    parser = etree.XMLParser(
        recover=True,
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
    )
    try:
        root = etree.parse(BytesIO(xml_bytes), parser).getroot()
    except etree.XMLSyntaxError as exc:
        return {"xml_valid": False, "error": str(exc)}

    counts = Counter(_local_name(node.tag) for node in root.iter() if isinstance(node.tag, str))
    title_nodes = [
        node for node in root.iter()
        if _local_name(node.tag) in {"article-title", "title"}
    ]
    doi_nodes = [
        node for node in root.iter()
        if _local_name(node.tag) == "article-id"
        and node.get("pub-id-type", "").lower() == "doi"
    ]
    abstract_nodes = [node for node in root.iter() if _local_name(node.tag) == "abstract"]
    body_nodes = [node for node in root.iter() if _local_name(node.tag) == "body"]
    section_nodes = [node for node in root.iter() if _local_name(node.tag) == "sec"]
    ref_nodes = [node for node in root.iter() if _local_name(node.tag) in {"ref", "mixed-citation", "element-citation"}]

    def first_text(nodes):
        for node in nodes:
            text = " ".join(" ".join(node.itertext()).split())
            if text:
                return text[:1000]
        return ""

    body_text = " ".join(" ".join(n.itertext()) for n in body_nodes).strip()
    return {
        "xml_valid": True,
        "root_element": _local_name(root.tag),
        "title": first_text(title_nodes),
        "doi": first_text(doi_nodes),
        "abstract_present": bool(abstract_nodes),
        "body_present": bool(body_nodes),
        "body_character_count": len(body_text),
        "section_count": len(section_nodes),
        "reference_count": len(ref_nodes),
        "has_body_text": bool(body_text),
        "element_counts_sample": dict(counts.most_common(25)),
        "interpretation": (
            "Se detecta elemento body y texto: posible texto completo estructurado; "
            "revisar manualmente secciones y contenido."
            if body_text
            else "No se detectó texto dentro de body. Esta respuesta no demuestra que incluya el texto completo."
        ),
    }


def xml_to_text(xml_bytes: bytes) -> str:
    """Convierte el XML a texto plano orientativo, conservando el orden de lectura."""
    parser = etree.XMLParser(recover=True, resolve_entities=False, no_network=True)
    try:
        root = etree.parse(BytesIO(xml_bytes), parser).getroot()
    except etree.XMLSyntaxError:
        return xml_bytes.decode("utf-8", errors="replace")
    return "\n".join(
        line.strip()
        for line in " ".join(root.itertext()).splitlines()
        if line.strip()
    )
