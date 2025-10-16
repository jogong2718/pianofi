# ECS Cluster
resource "aws_ecs_cluster" "main" {
    name = var.cluster_name

    setting {
        name = "containerInsights"
        value = var.enable_container_insights ? "enabled" : "disabled"
    }

    tags = var.tags
}