select country, year, renewable_share_pct, wind_share_pct, solar_share_pct
from {{ ref('fct_energy_mix') }}
where renewable_share_pct < 0 or renewable_share_pct > 100
   or wind_share_pct < 0 or wind_share_pct > 100
   or solar_share_pct < 0 or solar_share_pct > 100