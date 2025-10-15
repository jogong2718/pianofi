resource "aws_s3_bucket_policy" "tfer--pianofi-emails" {
  bucket = "pianofi-emails"
  policy = "{\"Statement\":[{\"Action\":\"s3:PutObject\",\"Condition\":{\"StringEquals\":{\"aws:Referer\":\"960370336558\"}},\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"ses.amazonaws.com\"},\"Resource\":\"arn:aws:s3:::pianofi-emails/*\",\"Sid\":\"GiveSESPermissionToWriteEmail\"}],\"Version\":\"2012-10-17\"}"
}
