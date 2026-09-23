provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  # s3_use_path_style         = true

  endpoints {
    dynamodb = "http://localhost:4566"
    events   = "http://localhost:4566"
    lambda   = "http://localhost:4566"
    apigateway = "http://localhost:4566"
    iam      = "http://localhost:4566"
  }
}

resource "aws_dynamodb_table" "contratos" {
  name           = "Contratos"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id_contrato"

  attribute {
    name = "id_contrato"
    type = "S"
  }
}

resource "aws_cloudwatch_event_bus" "pod99" {
  name = "pod99-event-bus"
}

resource "aws_iam_role" "lambda_role" {
  name = "pod99-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "pod99-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:ConditionCheckItem"
        ]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.contratos.arn
      },
      {
        Action = [
          "events:PutEvents"
        ]
        Effect   = "Allow"
        Resource = aws_cloudwatch_event_bus.pod99.arn
      }
    ]
  })
}
