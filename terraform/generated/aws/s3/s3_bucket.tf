resource "aws_s3_bucket" "tfer--pianofi" {
  bucket = "pianofi"

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "POST", "PUT"]
    allowed_origins = ["http://localhost:3000", "https://pianofi.ca", "https://www.pianofi.ca"]
    max_age_seconds = "0"
  }

  force_destroy = "false"

  grant {
    id          = "be7762f37923f3bdc3a4f3c66591b999a4bb1d1c26127deefdf1890aa24a7905"
    permissions = ["FULL_CONTROL"]
    type        = "CanonicalUser"
  }

  object_lock_enabled = "false"
  request_payer       = "BucketOwner"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }

      bucket_key_enabled = "true"
    }
  }

  tags = {
    application    = ""
    awsApplication = "arn:aws:resource-groups:us-east-1:960370336558:group/pianofi-application/0d00zy05xxefqp9rlmu7nm94ol"
  }

  tags_all = {
    application    = ""
    awsApplication = "arn:aws:resource-groups:us-east-1:960370336558:group/pianofi-application/0d00zy05xxefqp9rlmu7nm94ol"
  }

  versioning {
    enabled    = "false"
    mfa_delete = "false"
  }
}

resource "aws_s3_bucket" "tfer--pianofi-emails" {
  bucket        = "pianofi-emails"
  force_destroy = "false"

  grant {
    id          = "be7762f37923f3bdc3a4f3c66591b999a4bb1d1c26127deefdf1890aa24a7905"
    permissions = ["FULL_CONTROL"]
    type        = "CanonicalUser"
  }

  object_lock_enabled = "false"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": "s3:PutObject",
      "Condition": {
        "StringEquals": {
          "aws:Referer": "960370336558"
        }
      },
      "Effect": "Allow",
      "Principal": {
        "Service": "ses.amazonaws.com"
      },
      "Resource": "arn:aws:s3:::pianofi-emails/*",
      "Sid": "GiveSESPermissionToWriteEmail"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  request_payer = "BucketOwner"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }

      bucket_key_enabled = "true"
    }
  }

  versioning {
    enabled    = "false"
    mfa_delete = "false"
  }
}
