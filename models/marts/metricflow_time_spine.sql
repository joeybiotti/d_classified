{{
    config(
        materialized = 'table',
    )
}}

with days as (
    {{
        dbt_utils.date_spine(
            'day',
            "to_date('2020-01-01')",
            "to_date('2030-01-01')"
        )
    }}
)

select
    cast(date_day as date) as date_day
from days