select country, year, count(*) as row_count
from {{ ref('stg_energy') }}
group by country, year
having count(*) > 1