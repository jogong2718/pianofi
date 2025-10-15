resource "aws_ecs_service" "tfer--pianofi-cluster_pianofi-amtworkers-service" {
  availability_zone_rebalancing = "ENABLED"

  capacity_provider_strategy {
    base              = "0"
    capacity_provider = "FARGATE_SPOT"
    weight            = "1"
  }

  cluster = "pianofi-cluster"

  deployment_circuit_breaker {
    enable   = "true"
    rollback = "true"
  }

  deployment_controller {
    type = "ECS"
  }

  deployment_maximum_percent         = "200"
  deployment_minimum_healthy_percent = "100"
  desired_count                      = "0"
  enable_ecs_managed_tags            = "true"
  enable_execute_command             = "false"
  health_check_grace_period_seconds  = "0"
  name                               = "pianofi-amtworkers-service"

  network_configuration {
    assign_public_ip = "true"
    security_groups  = ["sg-0684c71a39827694a"]
    subnets          = ["subnet-02adcfe12104cfa07", "subnet-0332525e6b5f7d899", "subnet-0403b1c9a10eeac73", "subnet-06b669bde6091a5a8", "subnet-0961aceb732861b9a", "subnet-0f9dff4c4a36400df"]
  }

  platform_version    = "1.4.0"
  scheduling_strategy = "REPLICA"
  task_definition     = "arn:aws:ecs:us-east-1:960370336558:task-definition/pianofi-amtworkers:28"
}

resource "aws_ecs_service" "tfer--pianofi-cluster_pianofi-backend-service" {
  availability_zone_rebalancing = "ENABLED"

  capacity_provider_strategy {
    base              = "0"
    capacity_provider = "FARGATE_SPOT"
    weight            = "1"
  }

  cluster = "pianofi-cluster"

  deployment_circuit_breaker {
    enable   = "true"
    rollback = "true"
  }

  deployment_controller {
    type = "ECS"
  }

  deployment_maximum_percent         = "200"
  deployment_minimum_healthy_percent = "100"
  desired_count                      = "1"
  enable_ecs_managed_tags            = "true"
  enable_execute_command             = "false"
  health_check_grace_period_seconds  = "0"

  load_balancer {
    container_name   = "backend"
    container_port   = "8000"
    target_group_arn = "arn:aws:elasticloadbalancing:us-east-1:960370336558:targetgroup/pianofi-backend-targets/a015614c742bc685"
  }

  name = "pianofi-backend-service"

  network_configuration {
    assign_public_ip = "true"
    security_groups  = ["sg-09b57c977b006aacf"]
    subnets          = ["subnet-0332525e6b5f7d899", "subnet-0961aceb732861b9a"]
  }

  platform_version    = "1.4.0"
  scheduling_strategy = "REPLICA"
  task_definition     = "arn:aws:ecs:us-east-1:960370336558:task-definition/pianofi-backend:34"
}

resource "aws_ecs_service" "tfer--pianofi-cluster_pianofi-picogenworkers-service" {
  availability_zone_rebalancing = "ENABLED"

  capacity_provider_strategy {
    base              = "0"
    capacity_provider = "Infra-ECS-Cluster-pianofi-cluster-f30f2ed7-AsgCapacityProvider-mVLxXpF0UGAL"
    weight            = "1"
  }

  cluster = "pianofi-cluster"

  deployment_circuit_breaker {
    enable   = "true"
    rollback = "true"
  }

  deployment_controller {
    type = "ECS"
  }

  deployment_maximum_percent         = "200"
  deployment_minimum_healthy_percent = "100"
  desired_count                      = "0"
  enable_ecs_managed_tags            = "true"
  enable_execute_command             = "false"
  health_check_grace_period_seconds  = "0"
  name                               = "pianofi-picogenworkers-service"

  network_configuration {
    assign_public_ip = "false"
    security_groups  = ["sg-0684c71a39827694a"]
    subnets          = ["subnet-02adcfe12104cfa07", "subnet-0332525e6b5f7d899", "subnet-0403b1c9a10eeac73", "subnet-06b669bde6091a5a8", "subnet-0961aceb732861b9a", "subnet-0f9dff4c4a36400df"]
  }

  ordered_placement_strategy {
    field = "attribute:ecs.availability-zone"
    type  = "spread"
  }

  ordered_placement_strategy {
    field = "instanceId"
    type  = "spread"
  }

  scheduling_strategy = "REPLICA"
  task_definition     = "arn:aws:ecs:us-east-1:960370336558:task-definition/pianofi-picogenworkers:25"
}
