from biosense.domain.services.normalization import (
    normalize_cancer_type,
    normalize_country,
    normalize_gene_symbol,
    normalize_region_code,
)


def test_normalize_cancer_type_english_synonyms() -> None:
    assert normalize_cancer_type("NSCLC") == "lung"
    assert normalize_cancer_type("non-small cell lung cancer") == "lung"
    assert normalize_cancer_type("Lung Adenocarcinoma") == "lung"
    assert normalize_cancer_type("Colorectal Cancer") == "colorectal"
    assert normalize_cancer_type("CRC") == "colorectal"
    assert normalize_cancer_type("hepatocellular carcinoma") == "liver"
    assert normalize_cancer_type("gastric cancer") == "stomach"


def test_normalize_cancer_type_korean_synonyms() -> None:
    assert normalize_cancer_type("폐암") == "lung"
    assert normalize_cancer_type("대장암") == "colorectal"
    assert normalize_cancer_type("유방암") == "breast"
    assert normalize_cancer_type("간암") == "liver"


def test_normalize_cancer_type_already_canonical() -> None:
    codes = (
        "lung", "colorectal", "breast", "liver",
        "stomach", "pancreatic", "ovarian", "prostate",
    )
    for code in codes:
        assert normalize_cancer_type(code) == code


def test_normalize_cancer_type_unknown_falls_back_to_other() -> None:
    assert normalize_cancer_type("melanoma") == "other"
    assert normalize_cancer_type("") == "other"


def test_normalize_gene_symbol_case_and_whitespace() -> None:
    assert normalize_gene_symbol(" kras ") == "KRAS"
    assert normalize_gene_symbol("Kras") == "KRAS"
    assert normalize_gene_symbol("EGFR") == "EGFR"


def test_normalize_gene_symbol_known_aliases() -> None:
    assert normalize_gene_symbol("p53") == "TP53"
    assert normalize_gene_symbol("HER2") == "ERBB2"


def test_normalize_gene_symbol_unknown_returned_uppercased() -> None:
    assert normalize_gene_symbol("madeupgene") == "MADEUPGENE"


def test_normalize_country_aliases() -> None:
    assert normalize_country("South Korea") == "KR"
    assert normalize_country("Republic of Korea") == "KR"
    assert normalize_country("Korea") == "KR"
    assert normalize_country("United States") == "US"
    assert normalize_country("USA") == "US"
    assert normalize_country("U.S.") == "US"


def test_normalize_country_unknown_returned_as_is() -> None:
    assert normalize_country("Japan") == "JAPAN"


def test_normalize_region_code_canonical_passthrough() -> None:
    assert normalize_region_code("KR-11") == "KR-11"


def test_normalize_region_code_numeric() -> None:
    assert normalize_region_code("11") == "KR-11"
    assert normalize_region_code("5") == "KR-05"


def test_normalize_region_code_korean_name() -> None:
    assert normalize_region_code("서울특별시") == "KR-11"
    assert normalize_region_code("부산") == "KR-26"


def test_normalize_region_code_unknown_falls_back() -> None:
    assert normalize_region_code("Atlantis") == "KR-00"
