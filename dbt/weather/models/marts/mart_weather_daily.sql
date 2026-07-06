with staged as (
    select * from {{ ref('stg_weather_forecast') }}
)

select
    location_id,
    location_name,
    forecast_date,
    min_temp,
    max_temp,
    max_temp - min_temp as temp_range,
    morning_forecast,
    afternoon_forecast,
    night_forecast,
    summary_forecast,
    {{ condition_category('morning_forecast') }}   as morning_condition,
    {{ condition_category('afternoon_forecast') }} as afternoon_condition,
    {{ condition_category('night_forecast') }}     as night_condition,
    {{ condition_category('summary_forecast') }}   as summary_condition,
    ingested_at
from staged
