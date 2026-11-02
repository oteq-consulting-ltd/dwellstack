# Dwellstack — Architecture & Data Model Decisions

**Project:** Dwellstack — Wolverhampton EPC Data Engineering  
**Date:** 26 October 2026  
**Phase:** 2 — Design  
**Status:** Draft — decisions agreed in principle; implementation pending

## 1. Project objectives

Build a credible, maintainable data-engineering solution using UK Energy Performance Certificate (EPC) data.

The project should demonstrate:

- Data architecture and modelling
- Google Cloud Platform (GCP) implementation
- Medallion Architecture
- Python-based ingestion and data profiling
- Incremental data processing
- Data-quality management
- SQL transformation engineering
- Testing, operational reliability and architectural decision-making

**Guiding principle:** Prefer the simplest architecture that meets the requirements. Avoid unnecessary infrastructure, premature optimisation and scope expansion.

## 2. Technology choices

| Component              | Technology              | Decision                                 |
| ---------------------- | ----------------------- | ---------------------------------------- |
| Data profiling         | Python / Pandas         | Adopted                                  |
| Raw file storage       | Google Cloud Storage    | Planned                                  |
| Analytical warehouse   | BigQuery                | Planned                                  |
| SQL transformations    | Dataform                | Planned                                  |
| Batch ingestion        | Python / Cloud Run Jobs | Proposed                                 |
| Scheduling             | Cloud Scheduler         | Optional, when required                  |
| Credentials            | Secret Manager          | When external API credentials are needed |
| Distributed processing | PySpark                 | Deferred                                 |

**Rationale:** The current Wolverhampton dataset contains approximately 120,000 certificates and does not justify distributed processing. BigQuery and Dataform provide the main production transformation capabilities.

## 3. Medallion Architecture

Implement three logical data layers.

### Bronze — Source-aligned data

**Purpose:** Preserve what was received from the source.

Responsibilities:

- Store source records with minimal transformation.
- Preserve source field values.
- Record ingestion metadata.
- Support traceability and reprocessing.
- Avoid applying analytical business rules.

Cloud Storage retains original source files. BigQuery Bronze tables provide source-aligned records for downstream processing.

### Silver — Standardised certificate history

**Purpose:** Provide a consistent, reusable certificate-level dataset.

Responsibilities:

- Standardise field names and data types.
- Preserve distinct EPC assessments.
- Deduplicate repeated certificate records.
- Retain nullable property identifiers.
- Apply data-quality checks and expose quality indicators.
- Process new records incrementally.
- Handle verified corrections according to defined source rules.

**Grain:** One row per unique EPC certificate identifier.

### Gold — Analytical models

**Purpose:** Provide datasets designed for specific analytical requirements.

Initial models:

1. Latest EPC certificate per identifiable property.
2. Certificate-level analytical summaries where required.

Responsibilities:

- Apply analytical eligibility rules.
- Select the latest inspected certificate per UPRN.
- Calculate reporting metrics.
- Provide documented grains and consumer-facing contracts.

**Grain of primary property model:** One row per UPRN.

## 4. Data-quality strategy

**Decision:** Inclusive Silver model (Option B).

Retain successfully interpreted certificate records even when individual fields contain known quality issues.

Examples:

- Missing UPRN
- Unexpected inspection/lodgement date relationships
- Invalid or missing optional values

Expose explicit quality flags rather than silently excluding records.

Gold models determine which records are eligible for their particular analytical purpose.

**Rationale:** A consistent, inclusive Silver contract is easier for future developers to understand and maintain than a complex classification of exceptions.

Technical ingestion or parsing failures are handled separately from ordinary record-level data-quality issues.

## 5. File ingestion and idempotency

**Decision:** Do not ingest byte-identical files more than once.

Calculate a SHA-256 checksum for each incoming source file.

If an identical file has already been successfully ingested:

- Skip duplicate storage and processing.
- Record the duplicate ingestion attempt.
- Preserve existing source data.

Maintain an ingestion manifest containing:

- Source filename
- File checksum
- Ingestion timestamp
- Processing status
- Cloud Storage object location

Only mark ingestion successful after the source file has been safely persisted.

**Rationale:** Prevent redundant processing while maintaining operational traceability.

**Important:** File-level deduplication does not replace certificate-level deduplication. Different files can contain overlapping certificate records.

## 6. Incremental processing

**Decision:** Prefer incremental Bronze-to-Silver processing.

Normal operation should process new or changed records rather than rebuilding the complete dataset every time.

Maintain the ability to perform a full rebuild from retained Bronze data when required.

**Rationale:**

- Scales more effectively as data volumes increase.
- Reduces unnecessary processing.
- Supports repeatable, recoverable pipelines.

**Dependency:** The implementation must reflect the EPC source's actual delivery model, including whether extracts are full snapshots or incremental releases.

## 7. Certificate change management

**Decision:** Use an incremental, SCD Type 1-style Silver certificate model.

The working understanding is that changes to a property's energy performance normally require a new assessment and certificate.

Official EPC guidance indicates that lodged certificates cannot simply be altered; an incorrect assessment may require a replacement certificate.

Expected behaviour:

| Source event                                  | Silver action                    |
| --------------------------------------------- | -------------------------------- |
| New certificate identifier                    | INSERT                           |
| Previously ingested certificate, unchanged    | NO OP                            |
| Verified legitimate update to existing record | UPDATE                           |
| Unexpected change to assessment details       | Flag and investigate             |
| New assessment for an existing property       | INSERT as a separate certificate |

Use BigQuery `MERGE` where appropriate.

**Rationale:** Preserve distinct assessments without introducing unnecessary version-history complexity for each certificate.

**Outstanding verification:**

- Source identifier stability and uniqueness
- Whether certificate status changes are exposed
- How cancelled or replaced certificates appear in public extracts
- Whether legitimate changes to existing published rows occur

Retained Bronze data provides the historical evidence required to investigate unexpected changes.

## 8. Latest certificate selection

**Decision:** Select the latest inspected certificate for each identifiable property.

Selection rules:

1. Exclude records without a UPRN from the property-level Gold model.
2. Partition by UPRN.
3. Order by `inspection_date` descending.
4. Break ties using `lodgement_datetime` descending.
5. Apply `certificate_number` as the final deterministic tie-breaker.
6. Retain one certificate per UPRN.

This rule belongs in Gold because it produces a specific analytical representation of a property's latest known assessment.

The certificate history remains available in Silver.

**Implementation pattern:** SQL `ROW_NUMBER()` window function.

## 9. Existing data-quality findings

Initial Wolverhampton profiling identified:

- Approximately 119,927 certificate records
- Approximately 80,046 distinct identifiable UPRNs
- 1,162 records without a UPRN (approximately 0.97%)
- 1,755 differences between the date portion of `lodgement_datetime` and `lodgement_date`
- 50 inspection-after-lodgement timestamp anomalies, sharing a common recorded lodgement timestamp

These findings should inform Silver quality checks and documentation.

They do not automatically justify excluding affected certificates.

## 10. Potential future data sources

Two HM Land Registry datasets have been identified:

- Transaction Unique Identifier and UPRN Lookup
- Price Paid Data yearly files

These could enable future analysis of property sale prices and EPC performance.

**Decision:** Keep these as reference sources for a possible extension. Do not expand the current MVP scope.

Future integration must account for incomplete historical lookup coverage, transaction-to-UPRN cardinality and temporal alignment between transactions and EPC assessments.

## 11. Proposed physical GCP structure

| Location          | Object                       | Purpose                             |
| ----------------- | ---------------------------- | ----------------------------------- |
| Cloud Storage     | Raw EPC files                | Original source preservation        |
| BigQuery `bronze` | `epc_certificates_raw`       | Source-aligned records              |
| BigQuery `silver` | `epc_certificates`           | Standardised certificate history    |
| BigQuery `gold`   | `epc_properties_latest`      | Latest assessment per UPRN          |
| BigQuery `gold`   | Additional analytical models | Reporting and aggregation as needed |

Exact dataset names, schemas, partitioning, clustering and deployment configuration remain to be finalised.

## 12. Outstanding design tasks

- [ ] Define the physical Bronze schema and ingestion metadata.
- [ ] Define the Silver schema, quality flags and uniqueness tests.
- [ ] Verify EPC source delivery and correction semantics.
- [ ] Define the incremental processing and recovery strategy.
- [ ] Define the Gold property model and eligibility rules.
- [ ] Decide BigQuery partitioning and clustering based on access patterns.
- [ ] Establish Dataform dependencies, assertions and deployment workflow.
- [ ] Implement and validate the pipeline.

## 13. Architecture principles

1. **Clarity over cleverness:** A future developer should understand the system without interpreting undocumented exceptions.
2. **Source fidelity:** Preserve the original evidence.
3. **Explicit contracts:** Define what each data layer guarantees.
4. **Idempotency:** Repeated processing should not produce unintended duplicates.
5. **Proportionate complexity:** Introduce infrastructure only when requirements justify it.
6. **Recoverability:** Retain the ability to rebuild derived datasets.
7. **Business rules belong where they serve a defined purpose:** Avoid mixing source standardisation with analytical modelling.
8. **Verify assumptions:** Source behaviour should inform implementation decisions, not the other way around.
