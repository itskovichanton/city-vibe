-- Функция покрытия времени интервалом (в т.ч. через полночь)
CREATE OR REPLACE FUNCTION place_interval_covers(open_t text, close_t text, t text)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT CASE
    WHEN open_t IS NULL OR close_t IS NULL OR t IS NULL THEN false
    WHEN open_t <= close_t THEN (t >= open_t AND t < close_t)
    ELSE (t >= open_t OR t < close_t)
  END;
$$;
