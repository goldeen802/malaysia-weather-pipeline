with source as (
    select * from {{ source('weather_raw', 'forecast') }}
),

deduped as (
    select
        location_id,
        location_name,
        forecast_date,
        morning_forecast,
        afternoon_forecast,
        night_forecast,
        summary_forecast,
        summary_when,
        min_temp,
        max_temp,
        ingested_at,
        row_number() over (
            partition by location_id, forecast_date
            order by ingested_at desc
        ) as row_num
    from source
)

select
    location_id,
    location_name,
    forecast_date,
    morning_forecast,
    afternoon_forecast,
    night_forecast,
    summary_forecast,
    summary_when,
    min_temp,
    max_temp,
    ingested_at
from deduped
where row_num = 1
