"""Canonicalization shared by the equivalence gate (bench/run_gate.py).

A "record" is the per-PMID <PubmedArticle> (or <PubmedBookArticle>) subtree.

Canonicalization rules (documented in README, applied identically to both sides):
  1. Drop the retrieval envelope: the XML declaration, the DOCTYPE, and the
     <PubmedArticleSet> wrapper element. These are per-response framing, not record
     content (the legacy serial fetch produces 100 envelopes, the batched fetch 1).
  2. Apply W3C Canonical XML (xml.etree.ElementTree.canonicalize): byte-stable
     attribute ordering and entity/whitespace-in-markup normalization.
  3. NO text content is altered: titles, abstracts, identifiers, MeSH terms,
     coordinates etc. are compared verbatim (strip_text=False).

No fields inside the PubmedArticle subtree are dropped.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

ARTICLE_TAGS = ("PubmedArticle", "PubmedBookArticle")


def extract_articles(xml_text: str) -> dict[str, ET.Element]:
    """Map PMID -> article element from a PubmedArticleSet (or bare article) document."""
    root = ET.fromstring(xml_text)
    if root.tag in ARTICLE_TAGS:
        articles = [root]
    elif root.tag == "PubmedArticleSet":
        articles = [child for child in root if child.tag in ARTICLE_TAGS]
    else:
        raise ValueError(f"unexpected root element: {root.tag}")
    out: dict[str, ET.Element] = {}
    for art in articles:
        pmid = art.findtext("MedlineCitation/PMID") or art.findtext(".//PMID")
        if pmid and pmid.strip():
            out[pmid.strip()] = art
    return out


def canonicalize(record: str | ET.Element) -> bytes:
    """Canonical bytes of a single per-PMID record for equivalence comparison."""
    if isinstance(record, ET.Element):
        el = record
    else:
        root = ET.fromstring(record)
        if root.tag == "PubmedArticleSet":
            articles = [child for child in root if child.tag in ARTICLE_TAGS]
            if len(articles) != 1:
                raise ValueError(
                    f"canonicalize expects exactly one record, found {len(articles)}"
                )
            el = articles[0]
        elif root.tag in ARTICLE_TAGS:
            el = root
        else:
            raise ValueError(f"unexpected root element: {root.tag}")
    raw = ET.tostring(el, encoding="unicode")
    return ET.canonicalize(xml_data=raw, strip_text=False).encode("utf-8")
