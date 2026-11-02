# Dwellstack — EPC Data Discovery Notes

**Phase:** 1 — Data Discovery & Profiling  
**Dataset:** Wolverhampton Domestic Energy Performance Certificates (EPC)  
**Records:** 119,927  
**Status:** Initial certificate chronology investigation completed

## Executive Summary

Initial profiling of 119,927 domestic Energy Performance Certificate (EPC) records for Wolverhampton identified two significant data-quality inconsistencies.

1,755 certificates (1.46%) contain conflicting lodgement dates, while 50 certificates (0.042%) have official lodgement timestamps preceding their recorded inspection dates. All 50 share an identical timestamp, suggesting a potential source-system or batch-processing issue.

The investigation establishes lodgement_datetime as the appropriate field for determining official certificate validity, based on the source data dictionary.

These findings demonstrate the value of systematic data profiling before analytical modelling. Further work will assess their impact on property-level reporting and produce reproducible evidence suitable for submission to the relevant EPC data steward.

## 1. Dataset Overview

- 119,927 certificate records across 93 source columns.
- `certificate_number` identifies individual EPC certificates.
- `uprn` identifies properties and can occur across multiple certificates.
- 1,162 certificates (0.97%) have missing UPRNs.
- Historical certificates must be retained, while property-level reporting requires a rule for selecting the latest certificate.

## 2. Date Field Definitions

Definitions taken from the EPC data dictionary:

| Field                | Definition                                                                      |
| -------------------- | ------------------------------------------------------------------------------- |
| `inspection_date`    | Date building information was collected to prepare the EPC                      |
| `lodgement_date`     | Date the certificate was added to the register                                  |
| `lodgement_datetime` | Official registration timestamp, determining when the certificate becomes valid |

All three date fields were successfully converted to Pandas datetime types, with no missing values identified.

## 3. DQ-001 — Conflicting Lodgement Dates

**Finding:** 1,755 certificates (1.46%) have a `lodgement_date` that differs from the calendar date of `lodgement_datetime`.

Initial chronology checks identified:

| Validation                                              | Affected records |
| ------------------------------------------------------- | ---------------: |
| Inspection after `lodgement_date`                       |            1,544 |
| Inspection after date derived from `lodgement_datetime` |               50 |

Using the official timestamp reduces apparent chronology anomalies by approximately 96.8%.

**Interpretation:** The fields are inconsistent for a subset of records. The data dictionary supports using `lodgement_datetime` for official certificate validity, but the cause of the discrepancy remains unverified.

**Proposed handling:**

- Preserve both source fields.
- Use `lodgement_datetime` for official lodgement chronology.
- Flag mismatches for data-quality reporting.
- Investigate whether discrepancies affect latest-certificate selection.

## 4. DQ-002 — Certificates Lodged Before Inspection

**Finding:** 50 certificates (0.042%) have an inspection date later than their official lodgement date.

All 50 share the exact timestamp:

`2020-09-20 15:21:18`

Inspection dates are distributed as follows:

| Inspection date | Certificates |
| --------------- | -----------: |
| 2020-09-21      |           18 |
| 2020-09-22      |           13 |
| 2020-09-23      |           19 |
| **Total**       |       **50** |

The discrepancies span 1–3 calendar days.

**Interpretation:** The identical timestamp suggests a common processing event, potentially involving batch loading, migration or timestamp assignment. The actual cause has not been established.

**Proposed handling:**

- Preserve the records and original timestamps.
- Flag the chronology violations.
- Check whether records share assessor, reporting or geographic attributes.
- Include the finding in the eventual data-quality report.

## 5. Provisional Modelling Decisions

1. Retain historical EPC certificates.
2. Use `uprn` as the property business identifier where available.
3. Use `lodgement_datetime` as the candidate ordering field for selecting the most recently lodged certificate per property.
4. Retain `inspection_date` separately to represent assessment chronology.
5. Preserve original source values and expose quality flags rather than silently correcting or excluding records.
6. Define deterministic tie-breaking rules for certificates sharing identical lodgement timestamps.

These decisions remain subject to further validation.

## 6. Outstanding Investigations

- Confirm distinct UPRN counts and multiple-certificate distributions.
- Assess whether date-field inconsistencies affect latest-certificate selection.
- Investigate the shared attributes of the 50 chronology anomalies.
- Establish deterministic certificate-selection rules.
- Document the coverage and limitations of the EPC dataset.
- Determine the appropriate EPC Register data steward for reporting confirmed discrepancies.

## 7. Key Outcome

Initial profiling has identified two reproducible data-quality findings affecting the Wolverhampton EPC extract.

The investigation demonstrates the importance of validating source semantics and temporal consistency before building analytical models.

**Next project activity:** Identify the latest certificate per UPRN using Pandas, then test the analytical impact of alternative date-ordering rules.
