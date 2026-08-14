with source as (
    select * from {{ ref('int_postings_current') }}
),

enriched as (
    select
        *,
        round((salary_min + salary_max) / 2, 0) as salary_midpoint,
        case
            when salary_max >= 150000 then 'Senior'
            when salary_max >= 120000 then 'Mid-Level'
            else 'Junior'
        end as experience_level,
        left(description, 100) as description_preview
    from source
    where salary_min is not null and salary_max is not null
)

select * from enriched