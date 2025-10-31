variable "cluster_name" {
    description = "ECS cluster name"
    type = string
}

variable "enable_container_insights" {
    description = "Enable container insights"
    type = bool
}

variable "tags" {
    description = "Tags to apply to the ECS cluster"
    type = map(string)
    
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "execution_role_arn" {
  description = "IAM role ARN for ECS task execution"
  type        = string
}

variable "task_role_arn" {
  description = "IAM role ARN for ECS tasks"
  type        = string
}

variable "services" {
    description = "Map of services to deploy"
    type = map(object({
        name = string
        image = string
        cpu = number
        memory = number
        launch_type = string
        gpu_required = bool
    }))
}