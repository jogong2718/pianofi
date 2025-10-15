resource "aws_ecs_task_definition" "tfer--task-definition-002F-pianofi-amtworkers" {
  container_definitions    = "[{\"environment\":[{\"name\":\"AWS_REGION\",\"value\":\"us-east-1\"},{\"name\":\"USE_LOCAL_STORAGE\",\"value\":\"false\"}],\"essential\":true,\"image\":\"960370336558.dkr.ecr.us-east-1.amazonaws.com/pianofi/amtworkers:b7122b2ab16ed1b221b505821606e4ed4e04dbc5\",\"logConfiguration\":{\"logDriver\":\"awslogs\",\"options\":{\"awslogs-group\":\"/ecs/pianofi-amtworkers\",\"awslogs-create-group\":\"true\",\"awslogs-region\":\"us-east-1\",\"awslogs-stream-prefix\":\"ecs\"}},\"mountPoints\":[],\"name\":\"amtworkers\",\"portMappings\":[],\"systemControls\":[],\"volumesFrom\":[]}]"
  cpu                      = "2048"
  enable_fault_injection   = "false"
  execution_role_arn       = "arn:aws:iam::960370336558:role/ecsTaskExecutionRole"
  family                   = "pianofi-amtworkers"
  memory                   = "4096"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn            = "arn:aws:iam::960370336558:role/pianofi-task-role"
  track_latest             = "false"
}

resource "aws_ecs_task_definition" "tfer--task-definition-002F-pianofi-backend" {
  container_definitions    = "[{\"environment\":[{\"name\":\"AWS_REGION\",\"value\":\"us-east-1\"},{\"name\":\"ENVIRONMENT\",\"value\":\"production\"}],\"essential\":true,\"image\":\"960370336558.dkr.ecr.us-east-1.amazonaws.com/pianofi/backend:b7122b2ab16ed1b221b505821606e4ed4e04dbc5\",\"logConfiguration\":{\"logDriver\":\"awslogs\",\"options\":{\"awslogs-create-group\":\"true\",\"awslogs-region\":\"us-east-1\",\"awslogs-stream-prefix\":\"ecs\",\"awslogs-group\":\"/ecs/pianofi-backend\"}},\"mountPoints\":[],\"name\":\"backend\",\"portMappings\":[{\"containerPort\":8000,\"hostPort\":8000,\"protocol\":\"tcp\"}],\"systemControls\":[],\"volumesFrom\":[]}]"
  cpu                      = "512"
  enable_fault_injection   = "false"
  execution_role_arn       = "arn:aws:iam::960370336558:role/ecsTaskExecutionRole"
  family                   = "pianofi-backend"
  memory                   = "1024"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn            = "arn:aws:iam::960370336558:role/pianofi-task-role"
  track_latest             = "false"
}

resource "aws_ecs_task_definition" "tfer--task-definition-002F-pianofi-picogenworkers" {
  container_definitions    = "[{\"environment\":[{\"name\":\"AWS_REGION\",\"value\":\"us-east-1\"},{\"name\":\"PICOGEN_QUEUE_NAME\",\"value\":\"picogen_job_queue\"},{\"name\":\"USE_LOCAL_STORAGE\",\"value\":\"false\"}],\"essential\":true,\"image\":\"960370336558.dkr.ecr.us-east-1.amazonaws.com/pianofi/picogenworkers:b7122b2ab16ed1b221b505821606e4ed4e04dbc5\",\"logConfiguration\":{\"logDriver\":\"awslogs\",\"options\":{\"awslogs-create-group\":\"true\",\"awslogs-region\":\"us-east-1\",\"awslogs-stream-prefix\":\"ecs\",\"awslogs-group\":\"/ecs/pianofi-picogenworkers\"}},\"mountPoints\":[],\"name\":\"picogenworkers\",\"portMappings\":[],\"resourceRequirements\":[{\"type\":\"GPU\",\"value\":\"1\"}],\"systemControls\":[],\"volumesFrom\":[]}]"
  cpu                      = "1024"
  enable_fault_injection   = "false"
  execution_role_arn       = "arn:aws:iam::960370336558:role/ecsTaskExecutionRole"
  family                   = "pianofi-picogenworkers"
  memory                   = "4096"
  network_mode             = "awsvpc"
  requires_compatibilities = ["EC2"]
  task_role_arn            = "arn:aws:iam::960370336558:role/pianofi-task-role"
  track_latest             = "false"
}
