select
    country,
    year,
    electricity_generation,
    round((renewables_electricity / nullif(electricity_generation, 0) * 100)::numeric, 1) as renewable_share_pct,
    round((wind_electricity / nullif(electricity_generation, 0) * 100)::numeric, 1)       as wind_share_pct,
    round((solar_electricity / nullif(electricity_generation, 0) * 100)::numeric, 1)      as solar_share_pct,
    round((
        (electricity_generation - lag(electricity_generation) over (partition by country order by year))
        / nullif(lag(electricity_generation) over (partition by country order by year), 0) * 100
    )::numeric, 1) as generation_growth_pct
from {{ ref('stg_energy') }}