# d_classified

An end-to-end analytics engineering project demonstrating job posting ingestion, transformation, and analysis.

## Architecture

```
Adzuna API
    ↓
[Python Ingest] → Raw Snowflake Table
    ↓
[dbt Snapshot] → SCD2 History Tracking
    ↓
[dbt Staging] → Current Records Only
    ↓
[dbt Intermediate] → Enrichment & Deduplication
    ↓
[dbt Marts] → Analytics-Ready Tables
```

## What It Does

- **Ingests** job postings from Adzuna API via Python script
- **Tracks history** with dbt snapshots (SCD Type 2) to capture salary/title changes over time
- **Transforms** raw data through staging → intermediate → marts layers
- **Enriches** postings with computed fields (salary midpoint, experience level)
- **Aggregates** postings by category with salary statistics
- **Tests** data quality at every layer (uniqueness, not-null, freshness)

## Tech Stack

- **Ingestion**: Python 3.12, requests, pandas, python-dotenv
- **Warehouse**: Snowflake
- **Transformation**: dbt 1.11.2, Jinja2
- **Testing**: pytest, dbt tests
- **Code Quality**: ruff (linting + formatting)
- **Task Runner**: Make

## Quick Start

### Setup

```bash
make install
```

### Run Ingestion

```bash
python scripts/ingest.py
```

Fetches job postings from Adzuna API and writes to `raw.postings`.

### Run Transformations

```bash
dbt snapshot  # Capture SCD2 history
dbt run       # Build all models
dbt test      # Validate data quality
```

### View Tests

```bash
dbt test --select fct_postings
```

### All Available Commands

```bash
make help
```

## Project Structure

```
d_classified/
├── scripts/
│   └── ingest.py              # Python ETL script
├── models/
│   ├── staging/               # Raw data cleaning & casting
│   │   └── stg_postings.sql
│   ├── intermediate/          # Business logic & enrichment
│   │   ├── int_postings_deduplicated.sql
│   │   └── int_postings_enriched.sql
│   └── marts/                 # Analytics-ready tables
│       ├── fct_postings.sql
│       ├── dim_companies.sql
│       ├── dim_categories.sql
│       └── agg_postings_by_category.sql
├── snapshots/
│   └── snap_postings.sql      # SCD2 snapshot for history
├── tests/
│   ├── test_ingest.py         # Python unit tests
│   └── models/staging/src_postings.yml  # dbt data tests
├── Makefile                   # Task automation
├── dbt_project.yml            # dbt configuration
└── requirements.txt           # Python dependencies
```

## Key Features

### SCD Type 2 Snapshot
Tracks all changes to job postings over time with:
- `dbt_valid_from`: When version became active
- `dbt_valid_to`: When version was superseded (NULL = current)
- `dbt_scd_id`: Unique version identifier

This enables historical salary/title analysis.

### Multi-Layer Transformation
- **Staging**: Filters to current records, casts types
- **Intermediate**: Deduplicates, enriches with computed fields
- **Marts**: Analytics tables (facts, dimensions, aggregates)

### Data Quality
- 8 dbt data tests covering uniqueness, not-null, freshness
- 7 pytest unit tests for ingestion logic
- Schema validation on Snowflake tables

### CI-Ready
- Makefile for consistent local/CI execution
- Clean error handling and logging
- Test failures block deployment

## Next Steps

- [ ] Add dbt docs: `dbt docs generate && dbt docs serve`
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Materialize marts as tables for performance
- [ ] Add custom dbt macros for reusable logic
- [ ] Snapshot company & category dimensions

## Dependencies

See `requirements.txt`. Key packages:
- dbt-snowflake==1.11.2
- snowflake-connector-python==4.7.1
- pandas==2.3.3
- pytest==9.1.1
- ruff==0.16.1

## Notes

- Requires Snowflake account & Adzuna API credentials (set in `.env`)
- Raw data lives in `D_CLASSIFIED.RAW.POSTINGS`
- Transformed data in `D_CLASSIFIED.STAGING/INTERMEDIATE/MARTS`
- Snapshots in `D_CLASSIFIED.SNAPSHOTS`