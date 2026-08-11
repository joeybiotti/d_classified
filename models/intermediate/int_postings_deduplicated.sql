with source as (
    select * from {{ ref('stg_postings') }}
),

ranked as (
    select
        *,
        row_number()
            over (partition by posting_id order by loaded_at desc)
            as rn
    from source
),

deduped as (
    select
        posting_id,
        title,
        company,
        location,
        salary_max,
        salary_min,
        description,
        created,
        category,
        redirect_url,
        loaded_at
    from ranked
    where rn = 1
)

select * from deduped