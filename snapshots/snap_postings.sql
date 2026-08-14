{% snapshot snap_postings %}

    {{
        config(
            target_schema='snapshots',
            unique_key='posting_id',
            strategy='check',
            check_cols=['salary_min', 'salary_max', 'description'],
        )
    }}

    select *
    from {{ ref('int_postings_deduplicated') }}

{% endsnapshot %}