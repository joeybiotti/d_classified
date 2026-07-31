# d_classified

### Tracking the job market like a data warehouse tracks inventory

This project ingests job posting data over time and models it into a warehouse that tracks how postings actually change — salary ranges get revised, descriptions get edited, listings open and close. Instead of only capturing a single snapshot, this project is built to track that drift over time using Slowly Changing Dimension (Type 2) patterns.

## Why this exists

Most portfolio data projects work with a single static dataset. This one is deliberately built around data that changes — because real-world data warehousing is about handling change, not just loading a clean CSV once.

## Data Source

Postings data is pulled from the [Adzuna API](https://developer.adzuna.com/), across a handful of relevant search terms, on a repeating basis — not a one-time pull — so that the same posting can be captured multiple times as it changes.

## Planned Architecture

- **Ingestion (Python)**: Pulls postings from the Adzuna API and appends each run's results to a raw table, preserving history rather than overwriting it.
- **Warehouse (Snowflake)**: Raw data lands in Snowflake rather than a local file, reflecting a real cloud warehouse setup.
- **Transformation (dbt)**: Staging, snapshot (SCD Type 2 tracking of salary/description/status changes), and mart layers, following the same staging → intermediate → marts pattern as [splice_dbt](https://github.com/joeybiotti/splice_dbt).
- **Semantic Layer (dbt)**: Core metrics (e.g., average salary, active posting count) defined once and exposed consistently, rather than recalculated ad hoc.

## Status

🚧 Early build — ingestion in progress.

## Tech Stack

* **Python**: Ingestion and API handling
* **Snowflake**: Cloud data warehouse
* **dbt**: Transformation, testing, and semantic layer 