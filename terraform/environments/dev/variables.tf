variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to use"
  type        = string
  default     = "bruce-dev"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}