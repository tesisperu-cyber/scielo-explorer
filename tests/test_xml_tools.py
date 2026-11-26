from scielo_explorer.xml_tools import inspect_xml, xml_to_text


SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<article>
  <front><article-meta>
    <article-id pub-id-type="doi">10.1234/example</article-id>
    <title-group><article-title>Example article</article-title></title-group>
    <abstract><p>Example abstract.</p></abstract>
  </article-meta></front>
  <body><sec><title>Methods</title><p>Methods text.</p></sec></body>
  <back><ref-list><ref id="r1">Reference one</ref></ref-list></back>
</article>"""


def test_inspect_xml_detects_body_and_references():
    report = inspect_xml(SAMPLE)
    assert report["xml_valid"] is True
    assert report["body_present"] is True
    assert report["section_count"] == 1
    assert report["reference_count"] >= 1
    assert report["doi"] == "10.1234/example"


def test_xml_to_text_extracts_text():
    text = xml_to_text(SAMPLE)
    assert "Methods text." in text
    assert "Example abstract." in text
