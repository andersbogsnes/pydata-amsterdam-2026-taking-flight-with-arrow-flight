resource "aws_s3tables_table_bucket" "pydata_demo" {
  name = var.table_bucket_name
}

resource "aws_iam_user" "flight_backend" {
  name = "arrow_flight_backend"
}

resource "aws_iam_user_policy" "flight_backend_s3tables" {
  name   = "s3tables-access"
  user   = aws_iam_user.flight_backend.name
  policy = data.aws_iam_policy_document.flight_backend_s3tables.json
}

data "aws_iam_policy_document" "flight_backend_s3tables" {
  statement {
    sid = "S3TablesAccess"
    actions = [
      "s3tables:GetTable",
      "s3tables:GetTableData",
      "s3tables:PutTableData",
      "s3tables:GetNamespace",
      "s3tables:ListTables",
      "s3tables:ListNamespaces",
      "s3tables:GetTableBucket",
      "s3tables:GetTableMetadataLocation",
    ]
    resources = [
      aws_s3tables_table_bucket.pydata_demo.arn,
      "${aws_s3tables_table_bucket.pydata_demo.arn}/*",
    ]
  }
}


resource "aws_iam_access_key" "flight_backend" {
  user = aws_iam_user.flight_backend.name
}
resource "aws_secretsmanager_secret" "flight_backend_creds" {
  name = "arrow-flight-backend/aws-creds"
}

resource "aws_secretsmanager_secret_version" "flight_backend_creds" {
  secret_id = aws_secretsmanager_secret.flight_backend_creds.id
  secret_string = jsonencode({
    access_key_id     = aws_iam_access_key.flight_backend.id
    secret_access_key = aws_iam_access_key.flight_backend.secret
  })
}
