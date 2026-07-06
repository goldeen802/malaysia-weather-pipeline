{#
  One row per (location, target date, issue date): the representative forecast a
  given day made for a given future date. Preserves the issue-date dimension that
  the staging model collapses, so forecast accuracy can be measured across lead times.
#}

with base as (
    select
        location_id,
        location_name,
        forecast_date,
        date(ingested_at, 'Asia/Kuala_Lumpur') as issue_date,
        min_temp,
        max_temp,
        summary_forecast,
        ingested_at
    from {{ source('weather_raw', 'forecast') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by location_id, forecast_date, issue_date
            order by ingested_at desc
        ) as row_num
    from base
)

select
    location_id,
    location_name,
    forecast_date as target_date,
    issue_date,
    date_diff(forecast_date, issue_date, day) as lead_time_days,
    min_temp,
    max_temp,
    {{ condition_category('summary_forecast') }} as summary_condition
from ranked
where row_num = 1
  and forecast_date >= issue_date
