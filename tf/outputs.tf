output "bucketname" {
  value = aws_s3tables_table_bucket.pydata_demo.name
}

output "catalog_uri" {
  value = "https://s3tables.${aws_s3tables_table_bucket.pydata_demo.region}.amazonaws.com/iceberg"
}

output "warehouse" {
  value = aws_s3tables_table_bucket.pydata_demo.arn
}