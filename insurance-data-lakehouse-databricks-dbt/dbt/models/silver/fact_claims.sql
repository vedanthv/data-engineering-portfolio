{{ config(materialized='table') }}

select
    c.claim_id,
    c.policy_id,
    cast(c.claim_amount as double) as claim_amount,
    c.claim_status,
    cast(c.loss_date as date) as loss_date,
    p.premium_amount
from {{ source('bronze', 'claims_bronze') }} c
left join {{ ref('dim_policy') }} p
  on c.policy_id = p.policy_id
where c.claim_id is not null
