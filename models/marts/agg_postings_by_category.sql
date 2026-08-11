with postings as (
    select
        category,
        company,
        salary_min,
        salary_max,
        salary_midpoint,
        (salary_max - salary_min) as salary_range
    from {{ ref('int_postings_enriched') }}
),

aggregated as (
    select
        category,
        count(*) as posting_count,
        count(distinct company) as company_count,
        round(avg(salary_midpoint), 0) as avg_salary,
        round(min(salary_min), 0) as min_salary,
        round(max(salary_max), 0) as max_salary,
        round(avg(salary_range), 0) as avg_range
    from postings
    group by category
    order by posting_count desc
)

select * from aggregated
