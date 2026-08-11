with categories as (
    select
        category,
        count(*) as posting_count,
        count(distinct company) as company_count,
        round(avg(salary_max), 0) as avg_salary_max,
        round(avg(salary_min), 0) as avg_salary_min
    from {{ ref('int_postings_deduplicated') }}
    where category is not null
    group by category
)

select * from categories
order by posting_count desc