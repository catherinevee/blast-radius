# Custom Blast Radius

A custom implementation of the [Blast Radius](https://github.com/28mm/blast-radius) application for creating interactive visualizations of Terraform dependency graphs. This application provides a modern, feature-rich alternative to the original with enhanced functionality and real-world Terraform examples.

## Visual Examples

### Interactive Dependency Graph
The application generates interactive dependency graphs that visualize the relationships between Terraform resources:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VPC Module    │───▶│  Public Subnet  │───▶│ Internet Gateway│
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Private Subnet  │───▶│  NAT Gateway    │───▶│  Route Table    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Security Group  │───▶│  EC2 Instance   │───▶│  RDS Database   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Multi-Tier Application Architecture
Complex infrastructure with multiple layers and dependencies:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Load Balancer                    │
│                         (ALB Module)                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Auto Scaling Group                          │
│                    (ASG Module)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ EC2 Instance│  │ EC2 Instance│  │ EC2 Instance│            │
│  │             │  │             │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RDS Database                                │
│                    (RDS Module)                                │
└─────────────────────────────────────────────────────────────────┘
```

### Web Interface Features
The interactive web interface provides:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Blast Radius - Terraform Dependencies        │
├─────────────────────────────────────────────────────────────────┤
│ [🔍 Search] [📊 Filter] [💾 Export] [⚙️ Settings]              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐              │   │
│  │  │ VPC │───▶│ SG  │───▶│ EC2 │───▶│ RDS │              │   │
│  │  └─────┘    └─────┘    └─────┘    └─────┘              │   │
│  │     │           │           │           │              │   │
│  │     ▼           ▼           ▼           ▼              │   │
│  │  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐              │   │
│  │  │Subnet│    │IAM  │    │ALB  │    │CW   │              │   │
│  │  └─────┘    └─────┘    └─────┘    └─────┘              │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Legend: VPC=Virtual Private Cloud, SG=Security Group,        │
│          EC2=Elastic Compute Cloud, RDS=Relational Database   │
│          ALB=Application Load Balancer, CW=CloudWatch         │
└─────────────────────────────────────────────────────────────────┘
```

### Resource Type Color Coding
Different resource types are color-coded for easy identification:

- 🔵 **Blue**: VPC and Networking (VPC, Subnets, Route Tables)
- 🟢 **Green**: Compute Resources (EC2, Lambda, ECS)
- 🟡 **Yellow**: Storage Resources (S3, RDS, EBS)
- 🔴 **Red**: Security Resources (IAM, Security Groups)
- 🟣 **Purple**: Monitoring Resources (CloudWatch, SNS)
- 🟠 **Orange**: Load Balancing (ALB, NLB, Target Groups)

### Output Format Examples
The application supports multiple output formats for different use cases:

#### HTML Output (Interactive)
```html
<!-- Interactive visualization with D3.js -->
<div id="blast-radius-graph">
  <svg width="1200" height="800">
    <!-- Interactive nodes and edges -->
    <g class="nodes">
      <circle class="node vpc" cx="100" cy="100" r="20"/>
      <circle class="node subnet" cx="300" cy="100" r="15"/>
      <!-- More nodes... -->
    </g>
    <g class="edges">
      <line class="edge" x1="120" y1="100" x2="285" y2="100"/>
      <!-- More edges... -->
    </g>
  </svg>
</div>
```

#### SVG Output (Vector Graphics)
```svg
<svg width="1200" height="800" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
            refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>
    </marker>
  </defs>
  <g class="graph">
    <!-- Graph content -->
  </g>
</svg>
```

#### JSON Output (Data Structure)
```json
{
  "nodes": [
    {
      "id": "vpc",
      "type": "aws_vpc",
      "name": "main-vpc",
      "position": {"x": 100, "y": 100},
      "color": "#4A90E2",
      "group": "networking"
    },
    {
      "id": "subnet",
      "type": "aws_subnet", 
      "name": "public-subnet",
      "position": {"x": 300, "y": 100},
      "color": "#4A90E2",
      "group": "networking"
    }
  ],
  "edges": [
    {
      "source": "vpc",
      "target": "subnet",
      "type": "dependency"
    }
  ]
}
```

## Overview

Custom Blast Radius is a Python-based tool that parses Terraform configurations and generates interactive dependency graphs. It supports multiple output formats including HTML, SVG, PNG, and JSON, and provides a web interface for exploring infrastructure dependencies.

## Features

- **Interactive Visualizations**: Generate interactive HTML diagrams with zoom, pan, and search capabilities
- **Multiple Output Formats**: Export diagrams as SVG, PNG, or JSON for integration with other tools
- **Web Interface**: Serve diagrams via a Flask web server for easy exploration
- **Real-world Examples**: Includes comprehensive Terraform examples using official registry modules
- **Docker Support**: Containerized deployment for consistent environments
- **Comprehensive Testing**: Full test suite with pytest
- **Modern Architecture**: Built with Python 3.11+ and modern dependencies

## Prerequisites

- Python 3.11 or higher
- Graphviz (for graph layout)
- Docker (optional, for containerized deployment)

## Quick Start

### Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd blast-radius
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run with a Terraform example:
```bash
python blast_radius.py --serve examples/aws-vpc
```

### Docker Deployment

The application can be deployed using Docker for consistent environments:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Container                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                Custom Blast Radius                      │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │              Flask Web Server                    │   │   │
│  │  │  Port: 5000                                     │   │   │
│  │  │  - Interactive Graph Viewer                      │   │   │
│  │  │  - Export Functionality                          │   │   │
│  │  │  - Search and Filter                             │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │              Terraform Parser                    │   │   │
│  │  │  - HCL2 Parser                                   │   │   │
│  │  │  - Dependency Extraction                         │   │   │
│  │  │  - Graph Generation                              │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │              Graphviz Engine                     │   │   │
│  │  │  - Layout Algorithms                             │   │   │
│  │  │  - SVG Generation                                │   │   │
│  │  │  - PNG Export                                    │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Host System                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Terraform Files │  │   Web Browser   │  │  Output Files   │ │
│  │ (Mounted Volume)│  │  (Port 5000)    │  │  (Shared Dir)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

1. Build the Docker image:
```bash
docker build -t custom-blast-radius .
```

2. Run the container:
```bash
docker run -p 5000:5000 -v $(pwd)/examples:/data:ro custom-blast-radius
```

## Terraform Examples

The application includes several comprehensive Terraform examples that demonstrate real-world infrastructure patterns using official Terraform registry modules:

### AWS VPC Example (`examples/aws-vpc/`)

A complete VPC setup with public and private subnets, using the official AWS VPC module:

```terraform
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"
  
  name = var.project_name
  cidr = var.vpc_cidr
  
  azs             = data.aws_availability_zones.available.names
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway = true
  single_nat_gateway = true
  
  enable_dns_hostnames = true
  enable_dns_support   = true
}
```

### Multi-Tier Application Example (`examples/multi-tier-app/`)

A three-tier application architecture using multiple registry modules:

```terraform
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"
  # VPC configuration
}

module "alb" {
  source = "terraform-aws-modules/alb/aws"
  version = "8.7.0"
  # ALB configuration
}

module "rds" {
  source = "terraform-aws-modules/rds/aws"
  version = "6.1.0"
  # RDS configuration
}
```

### Kubernetes Example (`examples/kubernetes/`)

EKS cluster setup using the official EKS module:

```terraform
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "19.15.3"
  
  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
}
```

### Serverless Example (`examples/serverless/`)

Serverless architecture using Lambda and API Gateway modules:

```terraform
module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"
  version = "4.7.1"
  
  function_name = var.function_name
  handler       = "index.handler"
  runtime       = "nodejs18.x"
}

module "api_gateway" {
  source = "terraform-aws-modules/apigateway-v2/aws"
  version = "2.2.2"
  
  name = var.api_name
}
```

## Usage

### Application Workflow
The application follows this workflow to generate dependency graphs:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Terraform Files │───▶│   HCL2 Parser   │───▶│  Parse Results  │
│ (main.tf, etc.) │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Graph Builder  │◀───│  Dependency     │◀───│  Resource       │
│                 │    │  Extractor      │    │  Analyzer       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Graphviz       │───▶│  Layout Engine  │───▶│  Positioned     │
│  Layout         │    │                 │    │  Graph          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  D3.js          │───▶│  Interactive    │───▶│  Web Interface  │
│  Visualization  │    │  Features       │    │  (HTML/SVG)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Export         │───▶│  Multiple       │───▶│  Output Files   │
│  Functions      │    │  Formats        │    │  (PNG/JSON)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Command Line Interface

```bash
# Generate and serve interactive diagram
python blast_radius.py --serve /path/to/terraform/directory

# Export diagram to different formats
python blast_radius.py --export /path/to/terraform/directory --format html
python blast_radius.py --export /path/to/terraform/directory --format svg
python blast_radius.py --export /path/to/terraform/directory --format png
python blast_radius.py --export /path/to/terraform/directory --format json

# Generate all formats
python blast_radius.py --export /path/to/terraform/directory --format all
```

### Web Interface

When using the `--serve` option, the application starts a web server (default: http://localhost:5000) that provides:

- Interactive dependency graph visualization
- Zoom and pan controls
- Search functionality
- Node highlighting
- Resource type filtering
- Export options

## Project Structure

```
blast-radius/
├── blast_radius.py          # Main application script
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Multi-service Docker setup
├── Makefile                # Build and deployment automation
├── README.md               # This file
├── examples/               # Terraform examples
│   ├── aws-vpc/           # AWS VPC example
│   ├── multi-tier-app/    # Multi-tier application
│   ├── kubernetes/        # EKS cluster example
│   └── serverless/        # Serverless architecture
├── tests/                 # Test suite
│   └── test_blast_radius.py
└── output/                # Generated diagrams (created at runtime)
```

## Development

### Setting Up Development Environment

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -r requirements.txt
```

3. Run tests:
```bash
pytest tests/
```

### Code Style

The project uses:
- **Black** for code formatting
- **Flake8** for linting
- **pytest** for testing

Format code before committing:
```bash
black blast_radius.py tests/
flake8 blast_radius.py tests/
```

## API Reference

### BlastRadius Class

The main class for generating dependency graphs:

```python
from blast_radius import BlastRadius

# Initialize with Terraform directory
br = BlastRadius("/path/to/terraform/directory")

# Parse Terraform files
br.parse_terraform()

# Generate graph
graph = br.generate_graph()

# Export to different formats
br.export_html("output.html")
br.export_svg("output.svg")
br.export_png("output.png")
br.export_json("output.json")
```

### Command Line Options

- `--serve <directory>`: Start web server for interactive visualization
- `--export <directory>`: Export diagram to file(s)
- `--format <format>`: Output format (html, svg, png, json, all)
- `--host <host>`: Web server host (default: localhost)
- `--port <port>`: Web server port (default: 5000)
- `--output <directory>`: Output directory for exported files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Original Blast Radius project by [28mm](https://github.com/28mm/blast-radius)
- D3.js for interactive visualizations
- Graphviz for graph layout algorithms
- Terraform community for registry modules

## Support

For issues and questions:
- Check the examples directory for usage patterns
- Review the test suite for implementation details
- Open an issue on the repository

## Key Improvements Over Original

- **Modern Python**: Built with Python 3.11+ and modern dependencies
- **Registry Modules**: Examples use official Terraform registry modules
- **Enhanced Testing**: Comprehensive test suite with pytest
- **Docker Support**: Containerized deployment for consistency
- **Better Documentation**: Detailed documentation without emoticons
- **Real-world Examples**: Practical Terraform configurations
- **Improved Error Handling**: Better error messages and debugging
- **Performance Optimizations**: Faster parsing and rendering