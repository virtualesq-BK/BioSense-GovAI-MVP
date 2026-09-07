from biosense.application.services.ontology_service import OntologyService
from biosense.domain.entities.ontology import OntologyEntityType


def test_resolve_finds_known_cancer_synonym_with_citation():
    service = OntologyService()

    mapping = service.resolve(OntologyEntityType.CANCER, "NSCLC")

    assert mapping is not None
    assert mapping.canonical_name == "non-small cell lung cancer"
    assert mapping.source_citation  # every mapping cites a real source


def test_resolve_returns_none_for_unmapped_term():
    service = OntologyService()

    mapping = service.resolve(OntologyEntityType.CANCER, "some unmapped disease")

    assert mapping is None


def test_all_mappings_have_non_empty_citation_and_synonyms():
    service = OntologyService()

    for mapping in service.all():
        assert mapping.source_citation.strip() != ""
        assert len(mapping.synonyms) >= 1


def test_by_entity_type_filters_correctly():
    service = OntologyService()

    genes = service.by_entity_type(OntologyEntityType.GENE)

    assert all(m.entity_type == OntologyEntityType.GENE for m in genes)
    assert any(m.canonical_name == "TP53" for m in genes)
