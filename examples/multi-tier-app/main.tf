# Multi-Tier Application Configuration using Terraform Registry Modules
# This example demonstrates a three-tier application architecture

terraform {
  required_version = "1.12.2"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.47.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# VPC Module from Terraform Registry
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr

  azs             = data.aws_availability_zones.available.names
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway = true
  single_nat_gateway = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = var.common_tags
}

# Application Load Balancer Module
module "alb" {
  source = "terraform-aws-modules/alb/aws"
  version = "8.7.0"

  name = "${var.project_name}-alb"

  load_balancer_type = "application"

  vpc_id          = module.vpc.vpc_id
  subnets         = module.vpc.public_subnets
  security_groups = [aws_security_group.alb.id]

  target_groups = [
    {
      name_prefix      = "app-"
      backend_protocol = "HTTP"
      backend_port     = 80
      target_type      = "instance"
      health_check = {
        enabled             = true
        interval            = 30
        path                = "/health"
        port                = "traffic-port"
        healthy_threshold   = 3
        unhealthy_threshold = 3
        timeout             = 6
        protocol            = "HTTP"
        matcher             = "200"
      }
    }
  ]

  http_tcp_listeners = [
    {
      port               = 80
      protocol           = "HTTP"
      target_group_index = 0
    }
  ]

  tags = var.common_tags
}

# Auto Scaling Group Module
module "asg" {
  source = "terraform-aws-modules/autoscaling/aws"
  version = "7.3.1"

  name = "${var.project_name}-asg"

  min_size                  = var.asg_min_size
  max_size                  = var.asg_max_size
  desired_capacity          = var.asg_desired_capacity
  wait_for_capacity_timeout = 0
  health_check_type         = "EC2"
  vpc_zone_identifier       = module.vpc.private_subnets

  # Launch template
  launch_template_name = "${var.project_name}-lt"
  update_default_version = true

  image_id          = data.aws_ami.amazon_linux.id
  instance_type     = var.instance_type

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    db_host = module.rds.db_instance_endpoint
    db_name = var.db_name
    db_user = var.db_username
  }))

  security_groups = [aws_security_group.app.id]

  # Target group ARNs
  target_group_arns = [module.alb.target_group_arns[0]]

  # Scaling policies
  scaling_policies = {
    cpu = {
      policy_type = "TargetTrackingScaling"
      target_tracking_configuration = {
        predefined_metric_specification = {
          predefined_metric_type = "ASGAverageCPUUtilization"
        }
        target_value = 75.0
      }
    }
  }

  tags = var.common_tags
}

# RDS Module
module "rds" {
  source = "terraform-aws-modules/rds/aws"
  version = "6.1.0"

  identifier = "${var.project_name}-db"

  engine               = "postgres"
  engine_version       = "14"
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage

  db_name  = var.db_name
  username = var.db_username
  port     = "5432"

  vpc_security_group_ids = [aws_security_group.rds.id]
  subnet_ids             = module.vpc.private_subnets

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  create_db_subnet_group = true

  tags = var.common_tags
}

# IAM Role for EC2 instances
module "iam_assumable_role" {
  source = "terraform-aws-modules/iam/aws//modules/iam-assumable-role"
  version = "5.9.0"

  trusted_role_services = ["ec2.amazonaws.com"]

  create_role = true
  role_name   = "${var.project_name}-ec2-role"
  role_requires_mfa = false

  custom_role_policy_arns = [
    aws_iam_policy.cloudwatch_policy.arn
  ]

  tags = var.common_tags
}

# IAM Policy for CloudWatch
resource "aws_iam_policy" "cloudwatch_policy" {
  name        = "${var.project_name}-cloudwatch-policy"
  description = "Policy for CloudWatch access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = ["arn:aws:logs:*:*:*"]
      }
    ]
  })
}

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-alb-sg"
  })
}

resource "aws_security_group" "app" {
  name_prefix = "${var.project_name}-app-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-app-sg"
  })
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-rds-sg"
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/ec2/${var.project_name}"
  retention_in_days = 7

  tags = var.common_tags
} 