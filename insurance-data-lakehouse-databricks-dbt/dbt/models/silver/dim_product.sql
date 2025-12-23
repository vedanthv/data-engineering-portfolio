{{ config(materialized='table') }}

select distinct
    product
from {{ source('bronze', 'policy_bronze') }}
where product is not null
