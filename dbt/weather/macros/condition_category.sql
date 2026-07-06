{#
  Maps a raw Malaysian Meteorological Department (Malay) forecast phrase into a
  clean English category. Keyword-based so it is robust to location suffixes like
  "di beberapa tempat" / "di kawasan pedalaman".
#}
{% macro condition_category(column_name) %}
    case
        when lower({{ column_name }}) like '%ribut petir%' then 'Thunderstorms'
        when lower({{ column_name }}) like '%tiada hujan%' then 'No rain'
        when lower({{ column_name }}) like '%hujan%'       then 'Rain'
        when lower({{ column_name }}) like '%berangin%'    then 'Windy'
        when lower({{ column_name }}) like '%mendung%'     then 'Cloudy'
        else 'Other'
    end
{% endmacro %}
