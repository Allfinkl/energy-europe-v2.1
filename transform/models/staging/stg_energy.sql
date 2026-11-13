select
    country,
    year,
    electricity_generation,
    renewables_electricity,
    wind_electricity,
    solar_electricity,
    ingested_at
from {{ source('raw', 'energy') }}
where electricity_generation is not null