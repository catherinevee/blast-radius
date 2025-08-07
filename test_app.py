#!/usr/bin/env python3
"""
Simple test script for Blast Radius application
"""

import sys
import os
from pathlib import Path

def test_import():
    """Test that the application can be imported"""
    try:
        from blast_radius import BlastRadius
        print("✓ BlastRadius class imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import BlastRadius: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    try:
        from blast_radius import BlastRadius
        
        # Test initialization
        br = BlastRadius("/tmp")
        print("✓ BlastRadius initialized successfully")
        
        # Test node color assignment
        color = br._get_node_color("aws_vpc")
        assert color == "#FF6B6B"
        print("✓ Node color assignment works")
        
        # Test node shape assignment
        shape = br._get_node_shape("aws_vpc")
        assert shape == "box"
        print("✓ Node shape assignment works")
        
        # Test node group assignment
        group = br._get_node_group("aws_vpc")
        assert group == "networking"
        print("✓ Node group assignment works")
        
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def test_terraform_parsing():
    """Test Terraform parsing with a simple example"""
    try:
        import tempfile
        from blast_radius import BlastRadius
        
        # Create a temporary Terraform file
        with tempfile.TemporaryDirectory() as temp_dir:
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
            
            # Parse the Terraform files
            br = BlastRadius(temp_dir)
            br.parse_terraform()
            
            # Check that resources were parsed
            assert "aws_vpc.main" in br.resources
            assert "aws_subnet.main" in br.resources
            assert "region" in br.variables
            assert "vpc_id" in br.outputs
            
            print("✓ Terraform parsing works")
            
            # Test graph generation
            graph = br.generate_graph()
            assert len(graph.nodes) > 0
            print("✓ Graph generation works")
            
            return True
    except Exception as e:
        print(f"✗ Terraform parsing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Custom Blast Radius Application")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_import),
        ("Basic Functionality Test", test_basic_functionality),
        ("Terraform Parsing Test", test_terraform_parsing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"✗ {test_name} failed")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The application is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 