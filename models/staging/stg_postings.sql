with source as (
    select * from {{ source('raw', 'postings') }}
),

renamed as (
    select
        posting_id,
        title,
        company,
        location,
        salary_min,
        salary_max,
        description,
        cast(created as timestamp_ntz) as created,
        category,
        redirect_url,
        cast(loaded_at as timestamp_ntz) as loaded_at

    from source
)

select * from renamed