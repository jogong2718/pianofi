resource "aws_ecs_cluster" "tfer--pianofi-cluster" {
  name = "pianofi-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = {
    awsApplication = "arn:aws:resource-groups:us-east-1:960370336558:group/pianofi-application/0d00zy05xxefqp9rlmu7nm94ol"
  }

  tags_all = {
    awsApplication = "arn:aws:resource-groups:us-east-1:960370336558:group/pianofi-application/0d00zy05xxefqp9rlmu7nm94ol"
  }
}
