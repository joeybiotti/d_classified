with companies as (
    select
        company,
        count(*) as posting_count,
        count(distinct category) as category_count,
        round(avg(salary_max), 0) as avg_salary_max,
        round(avg(salary_min), 0) as avg_salary_min
    from {{ ref('int_postings_deduplicated') }}
    where company is not null
    group by company
)

select * from companies
order by posting_count desc