#!/usr/bin/env python3
"""
Custom Blast Radius - Interactive Terraform Dependency Graph Generator

A modern implementation of Blast Radius for creating interactive visualizations
of Terraform dependency graphs with support for multiple output formats.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import tempfile

try:
    import hcl2
    import networkx as nx
    import graphviz
    from flask import Flask, render_template_string, request, jsonify, send_from_directory
    from jinja2 import Template
except ImportError as e:
    print(f"Error: Missing required dependency - {e}")
    print("Please install dependencies with: pip install -r requirements.txt")
    sys.exit(1)


class BlastRadius:
    """Main class for generating Terraform dependency graphs."""
    
    def __init__(self, terraform_dir: str):
        """Initialize BlastRadius with Terraform directory."""
        self.terraform_dir = Path(terraform_dir)
        self.graph = nx.DiGraph()
        self.resources = {}
        self.data_sources = {}
        self.variables = {}
        self.outputs = {}
        self.modules = {}
        
    def parse_terraform(self) -> None:
        """Parse all Terraform files in the directory."""
        if not self.terraform_dir.exists():
            raise FileNotFoundError(f"Terraform directory not found: {self.terraform_dir}")
            
        # Find all .tf files
        tf_files = list(self.terraform_dir.glob("*.tf"))
        if not tf_files:
            raise ValueError(f"No .tf files found in {self.terraform_dir}")
            
        for tf_file in tf_files:
            try:
                with open(tf_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse HCL2 content
                parsed = hcl2.loads(content)
                
                # Extract different resource types
                for block in parsed:
                    if 'resource' in block:
                        for resource_type, resources in block['resource'].items():
                            for resource_name, resource_config in resources.items():
                                full_name = f"{resource_type}.{resource_name}"
                                self.resources[full_name] = {
                                    'type': resource_type,
                                    'name': resource_name,
                                    'config': resource_config,
                                    'file': str(tf_file)
                                }
                                
                    elif 'data' in block:
                        for data_type, data_sources in block['data'].items():
                            for data_name, data_config in data_sources.items():
                                full_name = f"data.{data_type}.{data_name}"
                                self.data_sources[full_name] = {
                                    'type': data_type,
                                    'name': data_name,
                                    'config': data_config,
                                    'file': str(tf_file)
                                }
                                
                    elif 'variable' in block:
                        for var_name, var_config in block['variable'].items():
                            self.variables[var_name] = {
                                'config': var_config,
                                'file': str(tf_file)
                            }
                            
                    elif 'output' in block:
                        for output_name, output_config in block['output'].items():
                            self.outputs[output_name] = {
                                'config': output_config,
                                'file': str(tf_file)
                            }
                            
                    elif 'module' in block:
                        for module_name, module_config in block['module'].items():
                            self.modules[module_name] = {
                                'config': module_config,
                                'file': str(tf_file)
                            }
                            
            except Exception as e:
                print(f"Warning: Error parsing {tf_file}: {e}")
                continue
                
    def _extract_dependencies(self, config: Dict) -> Set[str]:
        """Extract dependencies from a resource configuration."""
        dependencies = set()
        
        def extract_refs(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'ref' and isinstance(value, list):
                        for ref in value:
                            if isinstance(ref, dict) and 'name' in ref:
                                dependencies.add(ref['name'])
                    else:
                        extract_refs(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_refs(item)
                    
        extract_refs(config)
        return dependencies
        
    def generate_graph(self) -> nx.DiGraph:
        """Generate NetworkX graph from parsed Terraform resources."""
        # Add all resources as nodes
        for resource_name, resource_info in self.resources.items():
            self.graph.add_node(resource_name, 
                              type='resource',
                              resource_type=resource_info['type'],
                              name=resource_info['name'],
                              file=resource_info['file'],
                              color=self._get_node_color(resource_info['type']),
                              shape=self._get_node_shape(resource_info['type']),
                              group=self._get_node_group(resource_info['type']))
                              
        # Add data sources as nodes
        for data_name, data_info in self.data_sources.items():
            self.graph.add_node(data_name,
                              type='data',
                              resource_type=data_info['type'],
                              name=data_info['name'],
                              file=data_info['file'],
                              color=self._get_node_color(data_info['type']),
                              shape=self._get_node_shape(data_info['type']),
                              group=self._get_node_group(data_info['type']))
                              
        # Add variables as nodes
        for var_name, var_info in self.variables.items():
            self.graph.add_node(var_name,
                              type='variable',
                              name=var_name,
                              file=var_info['file'],
                              color='#FFD700',  # Gold
                              shape='ellipse',
                              group='variables')
                              
        # Add outputs as nodes
        for output_name, output_info in self.outputs.items():
            self.graph.add_node(output_name,
                              type='output',
                              name=output_name,
                              file=output_info['file'],
                              color='#32CD32',  # LimeGreen
                              shape='ellipse',
                              group='outputs')
                              
        # Add modules as nodes
        for module_name, module_info in self.modules.items():
            self.graph.add_node(module_name,
                              type='module',
                              name=module_name,
                              file=module_info['file'],
                              color='#9370DB',  # MediumPurple
                              shape='box',
                              group='modules')
                              
        # Add edges based on dependencies
        for resource_name, resource_info in self.resources.items():
            dependencies = self._extract_dependencies(resource_info['config'])
            for dep in dependencies:
                if dep in self.graph.nodes:
                    self.graph.add_edge(dep, resource_name)
                    
        return self.graph
        
    def _get_node_color(self, resource_type: str) -> str:
        """Get color for resource type."""
        color_map = {
            # AWS Resources
            'aws_vpc': '#FF6B6B',
            'aws_subnet': '#4ECDC4',
            'aws_internet_gateway': '#45B7D1',
            'aws_nat_gateway': '#96CEB4',
            'aws_route_table': '#FFEAA7',
            'aws_security_group': '#DDA0DD',
            'aws_instance': '#98D8C8',
            'aws_lb': '#F7DC6F',
            'aws_rds_cluster': '#BB8FCE',
            'aws_iam_role': '#85C1E9',
            'aws_s3_bucket': '#F8C471',
            'aws_lambda_function': '#82E0AA',
            'aws_eks_cluster': '#F1948A',
            'aws_autoscaling_group': '#85C1E9',
            'aws_cloudwatch_log_group': '#F7DC6F',
            
            # Azure Resources
            'azurerm_virtual_network': '#FF6B6B',
            'azurerm_subnet': '#4ECDC4',
            'azurerm_network_interface': '#45B7D1',
            'azurerm_virtual_machine': '#96CEB4',
            'azurerm_app_service_plan': '#FFEAA7',
            'azurerm_app_service': '#DDA0DD',
            'azurerm_storage_account': '#98D8C8',
            'azurerm_sql_database': '#F7DC6F',
            'azurerm_kubernetes_cluster': '#BB8FCE',
            
            # Google Cloud Resources
            'google_compute_network': '#FF6B6B',
            'google_compute_subnetwork': '#4ECDC4',
            'google_compute_instance': '#96CEB4',
            'google_storage_bucket': '#F8C471',
            'google_container_cluster': '#BB8FCE',
            
            # Default
            'default': '#CCCCCC'
        }
        
        return color_map.get(resource_type, color_map['default'])
        
    def _get_node_shape(self, resource_type: str) -> str:
        """Get shape for resource type."""
        shape_map = {
            # Network resources
            'aws_vpc': 'box',
            'aws_subnet': 'box',
            'aws_internet_gateway': 'diamond',
            'aws_nat_gateway': 'diamond',
            'aws_route_table': 'box',
            'aws_security_group': 'ellipse',
            
            # Compute resources
            'aws_instance': 'box',
            'aws_lb': 'diamond',
            'aws_autoscaling_group': 'box',
            'aws_lambda_function': 'ellipse',
            'aws_eks_cluster': 'box',
            
            # Storage and database
            'aws_s3_bucket': 'cylinder',
            'aws_rds_cluster': 'cylinder',
            
            # Default
            'default': 'box'
        }
        
        return shape_map.get(resource_type, shape_map['default'])
        
    def _get_node_group(self, resource_type: str) -> str:
        """Get group for resource type."""
        if resource_type.startswith('aws_vpc') or resource_type.startswith('aws_subnet'):
            return 'networking'
        elif resource_type.startswith('aws_instance') or resource_type.startswith('aws_lb'):
            return 'compute'
        elif resource_type.startswith('aws_s3') or resource_type.startswith('aws_rds'):
            return 'storage'
        elif resource_type.startswith('aws_iam'):
            return 'security'
        elif resource_type.startswith('aws_lambda'):
            return 'serverless'
        elif resource_type.startswith('aws_eks'):
            return 'kubernetes'
        else:
            return 'other'
            
    def export_html(self, output_file: str) -> None:
        """Export graph as interactive HTML."""
        # Create D3.js visualization HTML
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Terraform Dependency Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .controls {
            margin-bottom: 20px;
            text-align: center;
        }
        .controls button {
            margin: 0 5px;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background: #007bff;
            color: white;
            cursor: pointer;
        }
        .controls button:hover {
            background: #0056b3;
        }
        .search-box {
            margin: 10px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 200px;
        }
        .legend {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .legend-item {
            display: inline-block;
            margin: 5px 15px;
        }
        .legend-color {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 5px;
            border-radius: 3px;
        }
        .node {
            cursor: pointer;
        }
        .node:hover {
            stroke: #333;
            stroke-width: 2px;
        }
        .link {
            stroke: #999;
            stroke-opacity: 0.6;
        }
        .tooltip {
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Terraform Dependency Graph</h1>
        
        <div class="controls">
            <button onclick="resetZoom()">Reset Zoom</button>
            <button onclick="exportSVG()">Export SVG</button>
            <button onclick="exportPNG()">Export PNG</button>
            <input type="text" class="search-box" placeholder="Search resources..." onkeyup="searchNodes(this.value)">
        </div>
        
        <div class="legend">
            <strong>Resource Types:</strong>
            <div class="legend-item"><span class="legend-color" style="background: #FF6B6B;"></span>Networking</div>
            <div class="legend-item"><span class="legend-color" style="background: #4ECDC4;"></span>Compute</div>
            <div class="legend-item"><span class="legend-color" style="background: #F8C471;"></span>Storage</div>
            <div class="legend-item"><span class="legend-color" style="background: #DDA0DD;"></span>Security</div>
            <div class="legend-item"><span class="legend-color" style="background: #9370DB;"></span>Modules</div>
            <div class="legend-item"><span class="legend-color" style="background: #FFD700;"></span>Variables</div>
            <div class="legend-item"><span class="legend-color" style="background: #32CD32;"></span>Outputs</div>
        </div>
        
        <div id="graph"></div>
    </div>

    <script>
        // Graph data
        const graphData = {{ graph_data | safe }};
        
        // Setup
        const width = 1000;
        const height = 600;
        const margin = {top: 20, right: 20, bottom: 20, left: 20};
        
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
            
        const g = svg.append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);
            
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });
            
        svg.call(zoom);
        
        // Force simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(30));
            
        // Links
        const link = g.append("g")
            .selectAll("line")
            .data(graphData.links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", 2);
            
        // Nodes
        const node = g.append("g")
            .selectAll("circle")
            .data(graphData.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", 8)
            .attr("fill", d => d.color)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
                
        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
            
        node.on("mouseover", function(event, d) {
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            tooltip.html(`<strong>${d.id}</strong><br/>Type: ${d.type}<br/>Group: ${d.group}`)
                .style("left", (event.pageX + 5) + "px")
                .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", function(d) {
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        });
        
        // Update positions
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
                
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
        });
        
        // Drag functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
        
        // Control functions
        function resetZoom() {
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
            );
        }
        
        function searchNodes(query) {
            const searchTerm = query.toLowerCase();
            node.style("opacity", d => 
                d.id.toLowerCase().includes(searchTerm) ? 1 : 0.3
            );
        }
        
        function exportSVG() {
            const svgData = new XMLSerializer().serializeToString(svg.node());
            const svgBlob = new Blob([svgData], {type: "image/svg+xml;charset=utf-8"});
            const svgUrl = URL.createObjectURL(svgBlob);
            const downloadLink = document.createElement("a");
            downloadLink.href = svgUrl;
            downloadLink.download = "terraform-dependency-graph.svg";
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        }
        
        function exportPNG() {
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
            const img = new Image();
            const svgData = new XMLSerializer().serializeToString(svg.node());
            const svgBlob = new Blob([svgData], {type: "image/svg+xml;charset=utf-8"});
            const url = URL.createObjectURL(svgBlob);
            
            img.onload = function() {
                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(img, 0, 0);
                const pngUrl = canvas.toDataURL("image/png");
                const downloadLink = document.createElement("a");
                downloadLink.href = pngUrl;
                downloadLink.download = "terraform-dependency-graph.png";
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
            };
            img.src = url;
        }
    </script>
</body>
</html>
        """
        
        # Convert graph to D3.js format
        graph_data = {
            'nodes': [],
            'links': []
        }
        
        for node, attrs in self.graph.nodes(data=True):
            graph_data['nodes'].append({
                'id': node,
                'type': attrs.get('type', 'unknown'),
                'group': attrs.get('group', 'other'),
                'color': attrs.get('color', '#CCCCCC')
            })
            
        for source, target in self.graph.edges():
            graph_data['links'].append({
                'source': source,
                'target': target
            })
            
        # Render template
        template = Template(html_template)
        html_content = template.render(graph_data=json.dumps(graph_data))
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    def export_svg(self, output_file: str) -> None:
        """Export graph as SVG."""
        dot = graphviz.Digraph(comment='Terraform Dependency Graph')
        dot.attr(rankdir='TB')
        
        # Add nodes
        for node, attrs in self.graph.nodes(data=True):
            dot.node(node, 
                    label=f"{attrs.get('name', node)}\n({attrs.get('type', 'unknown')})",
                    style='filled',
                    fillcolor=attrs.get('color', '#CCCCCC'),
                    shape=attrs.get('shape', 'box'))
                    
        # Add edges
        for source, target in self.graph.edges():
            dot.edge(source, target)
            
        # Render SVG
        dot.render(output_file, format='svg', cleanup=True)
        
    def export_png(self, output_file: str) -> None:
        """Export graph as PNG."""
        dot = graphviz.Digraph(comment='Terraform Dependency Graph')
        dot.attr(rankdir='TB')
        
        # Add nodes
        for node, attrs in self.graph.nodes(data=True):
            dot.node(node, 
                    label=f"{attrs.get('name', node)}\n({attrs.get('type', 'unknown')})",
                    style='filled',
                    fillcolor=attrs.get('color', '#CCCCCC'),
                    shape=attrs.get('shape', 'box'))
                    
        # Add edges
        for source, target in self.graph.edges():
            dot.edge(source, target)
            
        # Render PNG
        dot.render(output_file, format='png', cleanup=True)
        
    def export_json(self, output_file: str) -> None:
        """Export graph as JSON."""
        graph_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'terraform_dir': str(self.terraform_dir),
                'total_resources': len(self.resources),
                'total_data_sources': len(self.data_sources),
                'total_variables': len(self.variables),
                'total_outputs': len(self.outputs),
                'total_modules': len(self.modules)
            }
        }
        
        for node, attrs in self.graph.nodes(data=True):
            graph_data['nodes'].append({
                'id': node,
                'type': attrs.get('type', 'unknown'),
                'resource_type': attrs.get('resource_type', ''),
                'name': attrs.get('name', node),
                'group': attrs.get('group', 'other'),
                'color': attrs.get('color', '#CCCCCC'),
                'shape': attrs.get('shape', 'box'),
                'file': attrs.get('file', '')
            })
            
        for source, target in self.graph.edges():
            graph_data['edges'].append({
                'source': source,
                'target': target
            })
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2)
            
    def serve(self, host: str = 'localhost', port: int = 5000) -> None:
        """Serve interactive visualization via Flask web server."""
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            return render_template_string(self._get_html_template())
            
        @app.route('/graph-data')
        def graph_data():
            graph_data = {
                'nodes': [],
                'links': []
            }
            
            for node, attrs in self.graph.nodes(data=True):
                graph_data['nodes'].append({
                    'id': node,
                    'type': attrs.get('type', 'unknown'),
                    'group': attrs.get('group', 'other'),
                    'color': attrs.get('color', '#CCCCCC')
                })
                
            for source, target in self.graph.edges():
                graph_data['links'].append({
                    'source': source,
                    'target': target
                })
                
            return jsonify(graph_data)
            
        @app.route('/export/<format>')
        def export(format):
            if format == 'svg':
                with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
                    self.export_svg(tmp.name)
                    return send_from_directory(os.path.dirname(tmp.name), 
                                            os.path.basename(tmp.name),
                                            as_attachment=True,
                                            download_name='terraform-graph.svg')
            elif format == 'png':
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    self.export_png(tmp.name)
                    return send_from_directory(os.path.dirname(tmp.name), 
                                            os.path.basename(tmp.name),
                                            as_attachment=True,
                                            download_name='terraform-graph.png')
            elif format == 'json':
                with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
                    self.export_json(tmp.name)
                    return send_from_directory(os.path.dirname(tmp.name), 
                                            os.path.basename(tmp.name),
                                            as_attachment=True,
                                            download_name='terraform-graph.json')
            else:
                return jsonify({'error': 'Unsupported format'}), 400
                
        print(f"Starting web server at http://{host}:{port}")
        print("Press Ctrl+C to stop the server")
        app.run(host=host, port=port, debug=False)
        
    def _get_html_template(self) -> str:
        """Get HTML template for web interface."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Terraform Dependency Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .controls {
            margin-bottom: 20px;
            text-align: center;
        }
        .controls button {
            margin: 0 5px;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background: #007bff;
            color: white;
            cursor: pointer;
        }
        .controls button:hover {
            background: #0056b3;
        }
        .search-box {
            margin: 10px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 200px;
        }
        .legend {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .legend-item {
            display: inline-block;
            margin: 5px 15px;
        }
        .legend-color {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 5px;
            border-radius: 3px;
        }
        .node {
            cursor: pointer;
        }
        .node:hover {
            stroke: #333;
            stroke-width: 2px;
        }
        .link {
            stroke: #999;
            stroke-opacity: 0.6;
        }
        .tooltip {
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Terraform Dependency Graph</h1>
        
        <div class="controls">
            <button onclick="resetZoom()">Reset Zoom</button>
            <button onclick="exportSVG()">Export SVG</button>
            <button onclick="exportPNG()">Export PNG</button>
            <button onclick="exportJSON()">Export JSON</button>
            <input type="text" class="search-box" placeholder="Search resources..." onkeyup="searchNodes(this.value)">
        </div>
        
        <div class="legend">
            <strong>Resource Types:</strong>
            <div class="legend-item"><span class="legend-color" style="background: #FF6B6B;"></span>Networking</div>
            <div class="legend-item"><span class="legend-color" style="background: #4ECDC4;"></span>Compute</div>
            <div class="legend-item"><span class="legend-color" style="background: #F8C471;"></span>Storage</div>
            <div class="legend-item"><span class="legend-color" style="background: #DDA0DD;"></span>Security</div>
            <div class="legend-item"><span class="legend-color" style="background: #9370DB;"></span>Modules</div>
            <div class="legend-item"><span class="legend-color" style="background: #FFD700;"></span>Variables</div>
            <div class="legend-item"><span class="legend-color" style="background: #32CD32;"></span>Outputs</div>
        </div>
        
        <div id="graph"></div>
    </div>

    <script>
        // Setup
        const width = 1000;
        const height = 600;
        const margin = {top: 20, right: 20, bottom: 20, left: 20};
        
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
            
        const g = svg.append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);
            
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });
            
        svg.call(zoom);
        
        // Load graph data
        d3.json("/graph-data").then(function(graphData) {
            // Force simulation
            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(30));
                
            // Links
            const link = g.append("g")
                .selectAll("line")
                .data(graphData.links)
                .enter().append("line")
                .attr("class", "link")
                .attr("stroke-width", 2);
                
            // Nodes
            const node = g.append("g")
                .selectAll("circle")
                .data(graphData.nodes)
                .enter().append("circle")
                .attr("class", "node")
                .attr("r", 8)
                .attr("fill", d => d.color)
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
                    
            // Tooltip
            const tooltip = d3.select("body").append("div")
                .attr("class", "tooltip")
                .style("opacity", 0);
                
            node.on("mouseover", function(event, d) {
                tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);
                tooltip.html(`<strong>${d.id}</strong><br/>Type: ${d.type}<br/>Group: ${d.group}`)
                    .style("left", (event.pageX + 5) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function(d) {
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            });
            
            // Update positions
            simulation.on("tick", () => {
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                    
                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
            });
            
            // Drag functions
            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }
            
            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }
            
            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
            
            // Control functions
            window.resetZoom = function() {
                svg.transition().duration(750).call(
                    zoom.transform,
                    d3.zoomIdentity
                );
            }
            
            window.searchNodes = function(query) {
                const searchTerm = query.toLowerCase();
                node.style("opacity", d => 
                    d.id.toLowerCase().includes(searchTerm) ? 1 : 0.3
                );
            }
            
            window.exportSVG = function() {
                window.open("/export/svg");
            }
            
            window.exportPNG = function() {
                window.open("/export/png");
            }
            
            window.exportJSON = function() {
                window.open("/export/json");
            }
        });
    </script>
</body>
</html>
        """


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Custom Blast Radius - Terraform Dependency Graph Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python blast_radius.py --serve examples/aws-vpc
  python blast_radius.py --export examples/multi-tier-app --format html
  python blast_radius.py --export examples/kubernetes --format all
        """
    )
    
    parser.add_argument('terraform_dir', 
                       help='Path to Terraform directory')
    parser.add_argument('--serve', action='store_true',
                       help='Start web server for interactive visualization')
    parser.add_argument('--export', action='store_true',
                       help='Export diagram to file(s)')
    parser.add_argument('--format', choices=['html', 'svg', 'png', 'json', 'all'],
                       default='html', help='Output format (default: html)')
    parser.add_argument('--host', default='localhost',
                       help='Web server host (default: localhost)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Web server port (default: 5000)')
    parser.add_argument('--output', default='output',
                       help='Output directory for exported files (default: output)')
    
    args = parser.parse_args()
    
    try:
        # Initialize BlastRadius
        br = BlastRadius(args.terraform_dir)
        
        # Parse Terraform files
        print(f"Parsing Terraform files in {args.terraform_dir}...")
        br.parse_terraform()
        
        # Generate graph
        print("Generating dependency graph...")
        graph = br.generate_graph()
        
        print(f"Graph generated with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        
        # Create output directory if needed
        if args.export:
            os.makedirs(args.output, exist_ok=True)
        
        # Handle different modes
        if args.serve:
            br.serve(host=args.host, port=args.port)
        elif args.export:
            if args.format == 'all':
                formats = ['html', 'svg', 'png', 'json']
            else:
                formats = [args.format]
                
            for fmt in formats:
                output_file = os.path.join(args.output, f"terraform-graph.{fmt}")
                print(f"Exporting {fmt} to {output_file}...")
                
                if fmt == 'html':
                    br.export_html(output_file)
                elif fmt == 'svg':
                    br.export_svg(output_file)
                elif fmt == 'png':
                    br.export_png(output_file)
                elif fmt == 'json':
                    br.export_json(output_file)
                    
            print(f"Export complete. Files saved to {args.output}/")
        else:
            # Default: serve
            br.serve(host=args.host, port=args.port)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 