"""Lightweight canonical-ontology synonym table (Phase 1).

Not a knowledge graph — a flat synonym/abbreviation lookup for the entity types
this phase touches (Cancer, Gene, Mutation, Biomarker, Sensor,
RecognitionMechanism), each mapping carrying its own source citation so nothing
here is an invented equivalence. Deliberately simple: `entity_type` +
`canonical` + `synonyms` is a shape a future Neo4j-backed graph (mentioned in
docs/DATA_ARCHITECTURE.md) can subsume without a rewrite — each row here would
become a node with SYNONYM_OF edges.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OntologyEntityType(str, Enum):
    CANCER = "cancer"
    GENE = "gene"
    MUTATION = "mutation"
    BIOMARKER = "biomarker"
    SENSOR = "sensor"
    RECOGNITION_MECHANISM = "recognition_mechanism"


@dataclass(frozen=True)
class OntologyMapping:
    entity_type: OntologyEntityType
    canonical_name: str
    synonyms: tuple[str, ...]
    source_citation: str
