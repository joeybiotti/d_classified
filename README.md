# d_classified

An end-to-end analytics engineering project demonstrating job posting ingestion, transformation, and analysis.

## Architecture

```
Adzuna API
    ↓
[Python Ingest] → Raw Snowflake Table
    ↓
[dbt Staging] → Cleaned & Typed Records
    ↓
[dbt Snapshot] → SCD2 History Tracking
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
- **CI**: GitHub Actions

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

### Generate a Chart

```bash
python scripts/visualize.py
```

Saves category/posting-volume charts to `assets/`.

### View Tests

```bash
dbt test --select fct_postings
```

### All Available Commands

```bash
make help
```

## Job Postings by Category

![Postings by Category](assets/postings_by_category.png)

## Project Structure

```
d_classified/
├── scripts/
│   ├── ingest.py               # Python ETL script
│   └── visualize.py            # Chart generation
├── models/
│   ├── staging/                 # Raw data cleaning & casting
│   │   └── stg_postings.sql
│   ├── intermediate/            # Business logic & enrichment
│   │   ├── int_postings_deduplicated.sql
│   │   └── int_postings_enriched.sql
│   └── marts/                   # Analytics-ready tables
│       ├── fct_postings.sql
│       ├── dim_companies.sql
│       ├── dim_categories.sql
│       ├── agg_postings_by_category.sql
│       └── _metrics.yml         # Semantic layer metrics
├── snapshots/
│   └── snap_postings.sql        # SCD2 snapshot for history
├── tests/
│   ├── test_ingest.py           # Python unit tests
│   └── models/staging/src_postings.yml  # dbt data tests
├── .github/workflows/
│   ├── tests.yml                # Python lint + pytest
│   └── dbt-ci.yml               # dbt build validation
├── Makefile                     # Task automation
├── dbt_project.yml              # dbt configuration
└── requirements.txt             # Python dependencies
```

## Key Features

### SCD Type 2 Snapshot
Tracks all changes to job postings over time with:
- `dbt_valid_from`: When version became active
- `dbt_valid_to`: When version was superseded (NULL = current)
- `dbt_scd_id`: Unique version identifier

This enables historical salary/title analysis.

### Multi-Layer Transformation
- **Staging**: Cleans and casts raw fields, one row per ingested record
- **Snapshot**: Captures point-in-time versions of each posting off staging, enabling SCD Type 2 history
- **Intermediate**: Deduplicates, enriches with computed fields
- **Marts**: Analytics tables (facts, dimensions, aggregates)

### Semantic Layer
Core metrics defined once and queryable consistently:
- `avg_salary` — average salary midpoint across postings
- `active_postings` — count of currently active postings

```bash
dbt sl query --metrics avg_salary --group-by metric_time__day
```

### Data Quality
- 8 dbt data tests covering uniqueness, not-null, freshness
- 7 pytest unit tests for ingestion logic
- Schema validation on Snowflake tables

### CI
- `tests.yml` — lints and runs Python unit tests on every push/PR
- `dbt-ci.yml` — validates the full dbt build against Snowflake on every push/PR
- Test/build failures block merge

## Documentation

View the dbt project documentation locally:

```bash
dbt docs generate
dbt docs serve
```

Opens `http://localhost:8000` with:
- **Lineage graph** — shows data flow from staging → intermediate → marts
- **Model documentation** — column descriptions and data types
- **Data tests** — what validations run on each model
- **Source freshness** — when raw data was last loaded

## Next Steps

- [ ] Airflow DAG to schedule recurring ingestion
- [ ] Deploy dbt docs to GitHub Pages
- [ ] Add custom dbt macros for reusable logic

## Dependencies

See `requirements.txt` for exact pinned versions.

## Notes

- Requires Snowflake account & Adzuna API credentials (set in `.env`)
- Raw data lives in `D_CLASSIFIED.RAW.POSTINGS`
- Transformed data in `D_CLASSIFIED.STAGING/INTERMEDIATE/MARTS`
- Snapshots in `D_CLASSIFIED.SNAPSHOTS`