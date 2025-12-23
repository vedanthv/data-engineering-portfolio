{{ config(materialized='table') }}

select
    invoice_id,
    policy_id,
    cast(invoice_amount as double) as invoice_amount,
    cast(invoice_date as date) as invoice_date,
    payment_status
from {{ source('bronze', 'billing_bronze') }}
where invoice_id is not null
