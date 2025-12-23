{{ config(materialized='table') }}

select
    policy_id,
    cast(policy_start_date as date) as policy_start_date,
    cast(policy_end_date as date)   as policy_end_date,
    cast(premium_amount as double)  as premium_amount,
    case
        when current_date between cast(policy_start_date as date)
                             and cast(policy_end_date as date)
        then 'ACTIVE'
        else 'EXPIRED'
    end as policy_status
from {{ source('bronze', 'policy_bronze') }}
where policy_id is not null
