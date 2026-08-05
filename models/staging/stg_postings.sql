with source as (
    select * from {{ source('raw', 'postings') }}
),

renamed as (
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
        cast(loaded_at as timestamp_ntz) as loaded_at
    from source
)

select * from renamed