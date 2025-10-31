output "cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "service_names" {
  description = "Map of service names"
  value = {
    for k, v in aws_ecs_service.services : k => v.name
  }
}

output "task_definition_arns" {
  description = "Map of task definition ARNs"
  value = {
    for k, v in aws_ecs_task_definition.services : k => v.arn
  }
}

output "log_group_names" {
  description = "Map of CloudWatch log group names"
  value = {
    for k, v in aws_cloudwatch_log_group.services : k => v.name
  }
}