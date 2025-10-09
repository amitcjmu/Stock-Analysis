-- Fix duplicate IP addresses in raw import records
-- This updates the second occurrence of IP 10.16.2.1 to 10.16.2.2

-- First, let's see what we have
SELECT 
    id,
    row_number,
    raw_data->>'Hostname' as hostname,
    raw_data->>'IP Address' as ip_address
FROM raw_import_records
WHERE data_import_id = (
    SELECT id FROM data_imports 
    ORDER BY created_at DESC 
    LIMIT 1
)
ORDER BY row_number;

-- Update the duplicate IP for Windbp002app2
UPDATE raw_import_records
SET 
    raw_data = jsonb_set(raw_data::jsonb, '{IP Address}', '"10.16.2.2"'::jsonb),
    cleansed_data = CASE 
        WHEN cleansed_data IS NOT NULL AND cleansed_data != '{}' 
        THEN jsonb_set(cleansed_data::jsonb, '{IP Address}', '"10.16.2.2"'::jsonb)
        ELSE cleansed_data
    END
WHERE 
    data_import_id = (
        SELECT id FROM data_imports 
        ORDER BY created_at DESC 
        LIMIT 1
    )
    AND raw_data->>'Hostname' = 'Windbp002app2'
    AND raw_data->>'IP Address' = '10.16.2.1';

-- Verify the fix
SELECT 
    row_number,
    raw_data->>'Hostname' as hostname,
    raw_data->>'IP Address' as ip_address
FROM raw_import_records
WHERE data_import_id = (
    SELECT id FROM data_imports 
    ORDER BY created_at DESC 
    LIMIT 1
)
ORDER BY row_number;


