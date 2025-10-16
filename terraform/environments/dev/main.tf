terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

#--------------------------------------------------------------
# Create Dev ECS Cluster
#--------------------------------------------------------------

module "ecs_cluster" {
  source = "../../modules/compute"

  cluster_name              = "pianofi-${var.environment}-cluster"
  enable_container_insights = true
  tags = {
    Environment = var.environment
    Project     = "pianofi"
    ManagedBy   = "Terraform"
  }
}
