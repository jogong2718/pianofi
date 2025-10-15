output "aws_ecs_cluster_tfer--pianofi-cluster_id" {
  value = "${aws_ecs_cluster.tfer--pianofi-cluster.id}"
}

output "aws_ecs_service_tfer--pianofi-cluster_pianofi-amtworkers-service_id" {
  value = "${aws_ecs_service.tfer--pianofi-cluster_pianofi-amtworkers-service.id}"
}

output "aws_ecs_service_tfer--pianofi-cluster_pianofi-backend-service_id" {
  value = "${aws_ecs_service.tfer--pianofi-cluster_pianofi-backend-service.id}"
}

output "aws_ecs_service_tfer--pianofi-cluster_pianofi-picogenworkers-service_id" {
  value = "${aws_ecs_service.tfer--pianofi-cluster_pianofi-picogenworkers-service.id}"
}

output "aws_ecs_task_definition_tfer--task-definition-002F-pianofi-amtworkers_id" {
  value = "${aws_ecs_task_definition.tfer--task-definition-002F-pianofi-amtworkers.id}"
}

output "aws_ecs_task_definition_tfer--task-definition-002F-pianofi-backend_id" {
  value = "${aws_ecs_task_definition.tfer--task-definition-002F-pianofi-backend.id}"
}

output "aws_ecs_task_definition_tfer--task-definition-002F-pianofi-picogenworkers_id" {
  value = "${aws_ecs_task_definition.tfer--task-definition-002F-pianofi-picogenworkers.id}"
}
