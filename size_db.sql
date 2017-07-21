SELECT TABLE_NAME AS "Table Name",
table_rows AS "Quant of Rows", ROUND( (
data_length + index_length
) /1024, 2 ) AS "Total Size Kb"
FROM information_schema.TABLES
WHERE information_schema.TABLES.table_schema = 'MyFlaskApp'
LIMIT 0 , 30
