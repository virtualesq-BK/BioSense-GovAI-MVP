import uuid
from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from biosense.infrastructure.persistence.postgres.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_user_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    org_name: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="researcher")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    biomarker_cases: Mapped[list["BiomarkerCase"]] = relationship(back_populates="user")


class CtDNA(Base):
    __tablename__ = "ctdna"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    biomarkers: Mapped[list["Biomarker"]] = relationship(back_populates="ctdna")


class Cancer(Base):
    __tablename__ = "cancers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_ko: Mapped[str | None] = mapped_column(Text)
    icd_code: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    biomarkers: Mapped[list["Biomarker"]] = relationship(
        secondary="cancer_biomarkers", back_populates="cancers"
    )
    public_health_features: Mapped[list["PublicHealthFeature"]] = relationship(
        back_populates="cancer"
    )


class Biomarker(Base):
    __tablename__ = "biomarkers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    ctdna_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ctdna.id"), nullable=False)
    gene_symbol: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    neo4j_id: Mapped[str | None] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    ctdna: Mapped["CtDNA"] = relationship(back_populates="biomarkers")
    cancers: Mapped[list["Cancer"]] = relationship(
        secondary="cancer_biomarkers", back_populates="biomarkers"
    )
    recognition_matches: Mapped[list["BiomarkerRecognitionMatch"]] = relationship(
        back_populates="biomarker"
    )
    papers: Mapped[list["Paper"]] = relationship(secondary="paper_biomarkers", back_populates="biomarkers")


class CancerBiomarker(Base):
    """Cancer HAS Biomarker"""

    __tablename__ = "cancer_biomarkers"

    cancer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cancers.id", ondelete="CASCADE"), primary_key=True)
    biomarker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biomarkers.id", ondelete="CASCADE"), primary_key=True
    )
    notes: Mapped[str | None] = mapped_column(Text)


class RecognitionStrategy(Base):
    __tablename__ = "recognition_strategies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    neo4j_id: Mapped[str | None] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    biomarker_matches: Mapped[list["BiomarkerRecognitionMatch"]] = relationship(
        back_populates="recognition_strategy"
    )
    sensor_uses: Mapped[list["RecognitionSensorUse"]] = relationship(
        back_populates="recognition_strategy"
    )


class BiomarkerRecognitionMatch(Base):
    """Biomarker MATCHES RecognitionStrategy"""

    __tablename__ = "biomarker_recognition_matches"

    biomarker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biomarkers.id", ondelete="CASCADE"), primary_key=True
    )
    recognition_strategy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recognition_strategies.id", ondelete="CASCADE"), primary_key=True
    )
    match_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    mechanism: Mapped[str | None] = mapped_column(Text)

    biomarker: Mapped["Biomarker"] = relationship(back_populates="recognition_matches")
    recognition_strategy: Mapped["RecognitionStrategy"] = relationship(
        back_populates="biomarker_matches"
    )


class Sensor(Base):
    __tablename__ = "sensors"
    __table_args__ = (UniqueConstraint("sensor_type", "name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sensor_type: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    neo4j_id: Mapped[str | None] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    recognition_uses: Mapped[list["RecognitionSensorUse"]] = relationship(back_populates="sensor")
    performances: Mapped[list["SensorPerformance"]] = relationship(back_populates="sensor")
    protocols: Mapped[list["Protocol"]] = relationship(back_populates="sensor")
    papers: Mapped[list["Paper"]] = relationship(secondary="paper_sensors", back_populates="sensors")


class RecognitionSensorUse(Base):
    """RecognitionStrategy USES Sensor"""

    __tablename__ = "recognition_sensor_uses"

    recognition_strategy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recognition_strategies.id", ondelete="CASCADE"), primary_key=True
    )
    sensor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sensors.id", ondelete="CASCADE"), primary_key=True
    )
    efficiency: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    recognition_strategy: Mapped["RecognitionStrategy"] = relationship(back_populates="sensor_uses")
    sensor: Mapped["Sensor"] = relationship(back_populates="recognition_uses")


class SensorPerformance(Base):
    """Sensor GENERATES Performance"""

    __tablename__ = "sensor_performances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)
    sensitivity: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    specificity: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    lod_value: Mapped[Decimal | None] = mapped_column(Numeric)
    lod_unit: Mapped[str | None] = mapped_column(Text)
    assay_conditions: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    measured_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    sensor: Mapped["Sensor"] = relationship(back_populates="performances")


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    published_at: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    ingestion_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    pdf_filename: Mapped[str | None] = mapped_column(Text)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    abstract: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    chunks: Mapped[list["PaperChunk"]] = relationship(back_populates="paper")
    biomarkers: Mapped[list["Biomarker"]] = relationship(
        secondary="paper_biomarkers", back_populates="papers"
    )
    sensors: Mapped[list["Sensor"]] = relationship(
        secondary="paper_sensors", back_populates="papers"
    )
    protocols: Mapped[list["Protocol"]] = relationship(back_populates="paper")


class PaperChunk(Base):
    __tablename__ = "paper_chunks"
    __table_args__ = (UniqueConstraint("paper_id", "chunk_index"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    paper: Mapped["Paper"] = relationship(back_populates="chunks")


class PaperBiomarker(Base):
    __tablename__ = "paper_biomarkers"

    paper_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True)
    biomarker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biomarkers.id", ondelete="CASCADE"), primary_key=True
    )


class PaperSensor(Base):
    __tablename__ = "paper_sensors"

    paper_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True)
    sensor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sensors.id", ondelete="CASCADE"), primary_key=True)


class Protocol(Base):
    __tablename__ = "protocols"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sensor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sensors.id", ondelete="SET NULL"))
    paper_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("papers.id", ondelete="SET NULL"))
    steps: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    reagents: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    duration_hours: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    sensor: Mapped["Sensor | None"] = relationship(back_populates="protocols")
    paper: Mapped["Paper | None"] = relationship(back_populates="protocols")


class PublicHealthFeature(Base):
    __tablename__ = "public_health_features"
    __table_args__ = (
        UniqueConstraint("region_code", "cancer_id", "feature_type", "data_year"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_code: Mapped[str] = mapped_column(Text, nullable=False)
    region_name_ko: Mapped[str | None] = mapped_column(Text)
    cancer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cancers.id"), nullable=False)
    feature_type: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False, server_default="per_100k")
    data_year: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(server_default=func.now())

    cancer: Mapped["Cancer"] = relationship(back_populates="public_health_features")


class BiomarkerCase(Base):
    __tablename__ = "biomarker_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cancer_type: Mapped[str] = mapped_column(Text, nullable=False)
    ctdna_class: Mapped[str] = mapped_column(Text, nullable=False)
    patient_age: Mapped[int] = mapped_column(Integer, nullable=False)
    region_code: Mapped[str] = mapped_column(Text, nullable=False)
    cancer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cancers.id"))
    biomarker_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("biomarkers.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="biomarker_cases")
    cancer: Mapped["Cancer | None"] = relationship()
    biomarker: Mapped["Biomarker | None"] = relationship()
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="biomarker_case")


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("biomarker_case_id", "rank"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    biomarker_case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biomarker_cases.id", ondelete="CASCADE"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    sensor_type: Mapped[str] = mapped_column(Text, nullable=False)
    recognition_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    sensor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sensors.id"))
    recognition_strategy_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("recognition_strategies.id")
    )
    protocol_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("protocols.id"))
    expected_sensitivity: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    expected_specificity: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    expected_lod_value: Mapped[Decimal | None] = mapped_column(Numeric)
    expected_lod_unit: Mapped[str | None] = mapped_column(Text)
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    experimental_protocol: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    biomarker_case: Mapped["BiomarkerCase"] = relationship(back_populates="recommendations")
    sensor: Mapped["Sensor | None"] = relationship()
    recognition: Mapped["RecognitionStrategy | None"] = relationship()
    protocol: Mapped["Protocol | None"] = relationship()


class GraphSyncLog(Base):
    __tablename__ = "graph_sync_log"
    __table_args__ = (UniqueConstraint("entity_type", "entity_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    neo4j_id: Mapped[str] = mapped_column(Text, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(server_default=func.now())


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    source: Mapped[str] = mapped_column(Text, nullable=False)
    records_extracted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_transformed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_embedded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_stored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    started_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class IngestionCache(Base):
    __tablename__ = "ingestion_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class PublicDataDocument(Base):
    __tablename__ = "public_data_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    data_year: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    chunks: Mapped[list["PublicDataChunk"]] = relationship(back_populates="document")


class PublicDataChunk(Base):
    __tablename__ = "public_data_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("public_data_documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    document: Mapped["PublicDataDocument"] = relationship(back_populates="chunks")


class LiteratureIngestionJob(Base):
    __tablename__ = "literature_ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    chunks_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class RagQueryLog(Base):
    __tablename__ = "rag_query_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    cancer_type: Mapped[str | None] = mapped_column(Text)
    biomarker_name: Mapped[str | None] = mapped_column(Text)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    chunks_retrieved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommendations: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    citations: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class RagEvaluation(Base):
    __tablename__ = "rag_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    precision_at_k: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    recall_at_k: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    citation_coverage: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    mrr: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    chunks_evaluated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


# Explicit index declarations for SQLAlchemy metadata awareness
Index("idx_paper_chunks_embedding", PaperChunk.embedding, postgresql_using="ivfflat")
Index("idx_public_data_chunks_embedding", PublicDataChunk.embedding, postgresql_using="ivfflat")
