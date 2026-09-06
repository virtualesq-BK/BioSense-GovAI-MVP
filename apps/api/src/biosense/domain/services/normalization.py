"""Canonical-form normalization for cross-source entities.

Different data sources name the same real-world thing differently — "lung cancer" vs
"NSCLC" vs "폐암", "KRAS" vs "kras", "South Korea" vs "KR". This module is the single
place those synonyms are resolved to one canonical form, so the knowledge graph and
recommendation engine never see two nodes for what is actually one entity.

These are deterministic alias-table lookups only — no inference, no fuzzy matching, no
guessing. An unmapped cancer type falls back to "other" (an explicit, honest "we don't
know" bucket, matching the existing convention in korean_health_clients.py); an
unmapped gene symbol or country name is returned trimmed/cased but otherwise
unchanged, since fabricating a canonical code for either would misrepresent data we
don't actually have a mapping for.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Cancer type canonicalization
# ---------------------------------------------------------------------------

# Ordered so longer/more specific aliases are not shadowed by short substrings
# (e.g. check "non-small cell lung" before "lung").
_CANCER_TYPE_ALIASES: tuple[tuple[str, str], ...] = (
    ("non-small cell lung", "lung"),
    ("nsclc", "lung"),
    ("lung carcinoma", "lung"),
    ("lung adenocarcinoma", "lung"),
    ("폐암", "lung"),
    ("폐", "lung"),
    ("lung", "lung"),
    ("colorectal", "colorectal"),
    ("crc", "colorectal"),
    ("colon", "colorectal"),
    ("rectal", "colorectal"),
    ("대장암", "colorectal"),
    ("대장", "colorectal"),
    ("breast carcinoma", "breast"),
    ("유방암", "breast"),
    ("유방", "breast"),
    ("breast", "breast"),
    ("hepatocellular", "liver"),
    ("liver carcinoma", "liver"),
    ("간암", "liver"),
    ("간", "liver"),
    ("liver", "liver"),
    ("gastric", "stomach"),
    ("위암", "stomach"),
    ("위", "stomach"),
    ("stomach", "stomach"),
    ("pancreatic", "pancreatic"),
    ("췌장암", "pancreatic"),
    ("췌장", "pancreatic"),
    ("prostate", "prostate"),
    ("전립선암", "prostate"),
    ("전립선", "prostate"),
    ("ovarian", "ovarian"),
    ("난소암", "ovarian"),
    ("난소", "ovarian"),
)

# Cancer types the current MVP scope (Phase 1: Korea + USA — lung, colorectal, breast)
# actively supports end-to-end. Others normalize fine but are not yet backed by
# seeded biomarker/sensor graph data.
CANCER_TYPE_CODES: frozenset[str] = frozenset(
    {code for _, code in _CANCER_TYPE_ALIASES}
)


def normalize_cancer_type(raw: str) -> str:
    """Map a free-text or coded cancer type to its canonical lowercase code.

    Falls back to "other" for anything unrecognized — never fabricates a category.
    """
    if not raw:
        return "other"
    lowered = raw.strip().lower()
    for alias, code in _CANCER_TYPE_ALIASES:
        if alias in lowered:
            return code
    return "other"


# ---------------------------------------------------------------------------
# Gene symbol canonicalization
# ---------------------------------------------------------------------------

# HGNC symbols are already the canonical form GDC/literature use; normalization here
# is limited to whitespace/case, plus a small table of common non-HGNC aliases that
# do appear in older literature.
_GENE_SYMBOL_ALIASES: dict[str, str] = {
    "P53": "TP53",
    "HER2": "ERBB2",
    "NEU": "ERBB2",
    "C-KIT": "KIT",
}


def normalize_gene_symbol(raw: str) -> str:
    """Canonicalize a gene symbol: uppercase, trimmed, common-alias resolved.

    Returns the input uppercased/trimmed unchanged if no alias applies — we do not
    invent an HGNC symbol for a gene we don't have a mapping for.
    """
    if not raw:
        return ""
    symbol = raw.strip().upper()
    return _GENE_SYMBOL_ALIASES.get(symbol, symbol)


# ---------------------------------------------------------------------------
# Country canonicalization (ISO 3166-1 alpha-2)
# ---------------------------------------------------------------------------

_COUNTRY_ALIASES: dict[str, str] = {
    "south korea": "KR",
    "republic of korea": "KR",
    "korea": "KR",
    "korea, republic of": "KR",
    "kr": "KR",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "u.s.": "US",
    "u.s.a.": "US",
    "us": "US",
}


def normalize_country(raw: str) -> str:
    """Map a free-text or coded country name to its ISO 3166-1 alpha-2 code.

    Returns the trimmed/uppercased input unchanged if unrecognized, rather than
    guessing — an unmapped country is surfaced as-is, not silently dropped or
    miscategorized.
    """
    if not raw:
        return ""
    lowered = raw.strip().lower()
    return _COUNTRY_ALIASES.get(lowered, raw.strip().upper())


# ---------------------------------------------------------------------------
# Korean region code canonicalization
# ---------------------------------------------------------------------------

_KR_REGION_NAME_TO_CODE: dict[str, str] = {
    "서울": "KR-11",
    "부산": "KR-26",
    "대구": "KR-27",
    "인천": "KR-28",
    "광주": "KR-29",
    "대전": "KR-30",
    "울산": "KR-31",
    "경기": "KR-41",
    "강원": "KR-42",
    "충북": "KR-43",
    "충남": "KR-44",
    "전북": "KR-45",
    "전남": "KR-46",
    "경북": "KR-47",
    "경남": "KR-48",
    "제주": "KR-49",
    "세종": "KR-50",
}


def normalize_region_code(raw: str) -> str:
    """Canonicalize a Korean region reference to its `KR-NN` code.

    Accepts a Korean region name, a bare numeric code, or an already-canonical
    `KR-NN` code. Falls back to `KR-00` (explicit "unknown region") for anything
    else — matching the existing convention in korean_health_clients.py.
    """
    code = (raw or "").strip()
    if code.startswith("KR-"):
        return code
    if code.isdigit():
        return f"KR-{code.zfill(2)}"
    for name, mapped in _KR_REGION_NAME_TO_CODE.items():
        if name in code:
            return mapped
    return "KR-00"
