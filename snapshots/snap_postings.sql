{% snapshot snap_postings %}

    {{
        config(
            target_schema='snapshots',
            unique_key='posting_id',
            strategy='timestamp',
            updated_at='loaded_at'
        )
    }}

    select 
        *
    from {{ source('raw', 'postings') }}

{% endsnapshot %}