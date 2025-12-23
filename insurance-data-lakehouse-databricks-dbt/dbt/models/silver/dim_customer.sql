{{ config(materialized="table") }}

select distinct policy_id, customer_name
from {{ source("bronze", "policy_bronze") }}
where customer_name is not null
