with snapshot_data as (
    select * from {{ ref('snap_postings') }}
),

current_records as (
    select
        posting_id,
        title,
        company,
        location,
        salary_max,
        salary_min,
        description,
        cast(created as timestamp_ntz) as created,
        category,
        redirect_url,
        cast(loaded_at as timestamp_ntz) as loaded_at,
        dbt_valid_from,
        dbt_valid_to
    from snapshot_data
    where dbt_valid_to is null
)

select * from current_records