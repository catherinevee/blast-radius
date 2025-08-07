#!/usr/bin/env python3
"""
Tests for Custom Blast Radius application
"""

import pytest
import tempfile
import os
from pathlib import Path
from blast_radius import BlastRadius


class TestBlastRadius:
    """Test cases for BlastRadius class"""

    def test_init(self):
        """Test BlastRadius initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            br = BlastRadius(temp_dir)
            assert br.terraform_dir == Path(temp_dir)
            assert br.graph is not None
            assert br.resources == {}
            assert br.data_sources == {}
            assert br.variables == {}
            assert br.outputs == {}
            assert br.modules == {}

    def test_parse_terraform_empty_directory(self):
        """Test parsing empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            br = BlastRadius(temp_dir)
            with pytest.raises(ValueError, match="No .tf files found"):
                br.parse_terraform()

    def test_parse_terraform_nonexistent_directory(self):
        """Test parsing nonexistent directory"""
        br = BlastRadius("/nonexistent/directory")
        with pytest.raises(FileNotFoundError):
            br.parse_terraform()

    def test_parse_terraform_valid_files(self):
        """Test parsing valid Terraform files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Terraform file
            tf_file = Path(temp_dir) / "main.tf"
            tf_content = '''
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "test-vpc"
  }
}

resource "aws_subnet" "main" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  tags = {
    Name = "test-subnet"
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

output "vpc_id" {
  value = aws_vpc.main.id
}
'''
            tf_file.write_text(tf_content)

            br = BlastRadius(temp_dir)
            br.parse_terraform()

            # Check that resources were parsed
            assert "aws_vpc.main" in br.resources
            assert "aws_subnet.main" in br.resources
            assert "region" in br.variables
            assert "vpc_id" in br.outputs

    def test_generate_graph(self):
        """Test graph generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Terraform file with dependencies
            tf_file = Path(temp_dir) / "main.tf"
            tf_content = '''
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "main" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

module "example" {
  source = "./example"
  vpc_id = aws_vpc.main.id
}
'''
            tf_file.write_text(tf_content)

            br = BlastRadius(temp_dir)
            br.parse_terraform()
            graph = br.generate_graph()

            # Check that nodes were added
            assert len(graph.nodes) > 0
            assert "aws_vpc.main" in graph.nodes
            assert "aws_subnet.main" in graph.nodes
            assert "example" in graph.nodes

    def test_export_json(self):
        """Test JSON export"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Terraform file
            tf_file = Path(temp_dir) / "main.tf"
            tf_content = '''
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
'''
            tf_file.write_text(tf_content)

            br = BlastRadius(temp_dir)
            br.parse_terraform()
            br.generate_graph()

            # Export to JSON
            output_file = Path(temp_dir) / "output.json"
            br.export_json(str(output_file))

            # Check that file was created
            assert output_file.exists()
            assert output_file.stat().st_size > 0

    def test_node_color_assignment(self):
        """Test node color assignment"""
        br = BlastRadius("/tmp")
        
        # Test AWS VPC color
        color = br._get_node_color("aws_vpc")
        assert color == "#FF6B6B"
        
        # Test default color
        color = br._get_node_color("unknown_resource")
        assert color == "#CCCCCC"

    def test_node_shape_assignment(self):
        """Test node shape assignment"""
        br = BlastRadius("/tmp")
        
        # Test VPC shape
        shape = br._get_node_shape("aws_vpc")
        assert shape == "box"
        
        # Test default shape
        shape = br._get_node_shape("unknown_resource")
        assert shape == "box"

    def test_node_group_assignment(self):
        """Test node group assignment"""
        br = BlastRadius("/tmp")
        
        # Test networking group
        group = br._get_node_group("aws_vpc")
        assert group == "networking"
        
        # Test compute group
        group = br._get_node_group("aws_instance")
        assert group == "compute"
        
        # Test other group
        group = br._get_node_group("unknown_resource")
        assert group == "other"


class TestBlastRadiusIntegration:
    """Integration tests for BlastRadius"""

    def test_full_workflow(self):
        """Test complete workflow from parsing to export"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a comprehensive Terraform configuration
            tf_file = Path(temp_dir) / "main.tf"
            tf_content = '''
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

data "aws_availability_zones" "available" {
  state = "available"
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"
  
  name = var.project_name
  cidr = "10.0.0.0/16"
  
  azs             = data.aws_availability_zones.available.names
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = true
}

resource "aws_security_group" "app" {
  name_prefix = "app-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "app" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"
  subnet_id     = module.vpc.private_subnets[0]
  
  vpc_security_group_ids = [aws_security_group.app.id]
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "instance_id" {
  value = aws_instance.app.id
}
'''
            tf_file.write_text(tf_content)

            # Run complete workflow
            br = BlastRadius(temp_dir)
            br.parse_terraform()
            graph = br.generate_graph()

            # Verify parsing results
            assert len(br.resources) == 2  # security_group and instance
            assert len(br.data_sources) == 1  # availability_zones
            assert len(br.variables) == 2  # aws_region and project_name
            assert len(br.outputs) == 2  # vpc_id and instance_id
            assert len(br.modules) == 1  # vpc module

            # Verify graph
            assert len(graph.nodes) >= 8  # All resources, data sources, variables, outputs, modules
            assert len(graph.edges) > 0  # Should have dependencies

            # Test export
            output_file = Path(temp_dir) / "test_output.json"
            br.export_json(str(output_file))
            assert output_file.exists()


if __name__ == "__main__":
    pytest.main([__file__]) 