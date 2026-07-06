{#
  Forecast accuracy: for each location + target date, compare each ahead-of-time
  forecast (lead_time_days >= 1) against the "actual" — the same-day forecast issued
  on the target date itself (lead_time_days = 0), used as the ground-truth proxy.

  Populates as soon as snapshots span at least two calendar days.
#}

with snapshots as (
    select * from {{ ref('int_forecast_snapshots') }}
),

actuals as (
    select
        location_id,
        target_date,
        min_temp as actual_min_temp,
        max_temp as actual_max_temp,
        summary_condition as actual_condition
    from snapshots
    where lead_time_days = 0
),

predictions as (
    select
        location_id,
        location_name,
        target_date,
        issue_date,
        lead_time_days,
        min_temp as predicted_min_temp,
        max_temp as predicted_max_temp,
        summary_condition as predicted_condition
    from snapshots
    where lead_time_days >= 1
)

select
    p.location_id,
    p.location_name,
    p.target_date,
    p.issue_date,
    p.lead_time_days,
    p.predicted_max_temp,
    a.actual_max_temp,
    p.predicted_max_temp - a.actual_max_temp        as max_temp_error,
    abs(p.predicted_max_temp - a.actual_max_temp)   as abs_max_temp_error,
    p.predicted_min_temp,
    a.actual_min_temp,
    p.predicted_min_temp - a.actual_min_temp        as min_temp_error,
    p.predicted_condition,
    a.actual_condition,
    p.predicted_condition = a.actual_condition      as condition_correct
from predictions p
inner join actuals a
    on  p.location_id = a.location_id
    and p.target_date = a.target_date
