-- Days between the actual and the promised delivery date (positive means late).
CREATE OR REPLACE FUNCTION olist.delivery_delay_days(delivered TIMESTAMP, estimated TIMESTAMP)
RETURNS NUMERIC
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT CASE
        WHEN delivered IS NULL THEN NULL
        ELSE ROUND((EXTRACT(EPOCH FROM (delivered - estimated)) / 86400.0)::numeric, 2)
    END;
$$;
