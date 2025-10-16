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