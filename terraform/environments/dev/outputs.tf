output "cluster_name" {
  description = "Dev cluster name"
  value       = module.ecs_cluster.cluster_name
}

output "cluster_arn" {
  description = "Dev cluster ARN"
  value       = module.ecs_cluster.cluster_arn
}

output "cluster_id" {
  description = "Dev cluster ID"
  value       = module.ecs_cluster.cluster_id
}

output "console_url" {
  description = "AWS Console URL"
  value       = "https://console.aws.amazon.com/ecs/v2/clusters/${module.ecs_cluster.cluster_name}?region=us-east-1"
}