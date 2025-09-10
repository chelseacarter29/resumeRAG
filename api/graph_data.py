import os
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
import pandas as pd
import numpy as np
import networkx as nx
from http.server import BaseHTTPRequestHandler

# Global variables for data (will be loaded on first request)
entities_df = None
relationships_df = None
communities_df = None
text_units_df = None
graph = None
resume_data = {}

DATA_DIR = Path(__file__).parent.parent / "graphrag-workspace" / "output"
INPUT_DIR = Path(__file__).parent.parent / "graphrag-workspace" / "input"

def load_data():
    """Load all GraphRAG output data"""
    global entities_df, relationships_df, communities_df, text_units_df, graph, resume_data
    
    try:
        # Load parquet files (only essential ones for Vercel)
        entities_df = pd.read_parquet(DATA_DIR / "entities.parquet")
        relationships_df = pd.read_parquet(DATA_DIR / "relationships.parquet")
        communities_df = pd.read_parquet(DATA_DIR / "community_reports.parquet")
        text_units_df = pd.read_parquet(DATA_DIR / "text_units.parquet")
        
        print(f"Loaded {len(entities_df)} entities")
        print(f"Loaded {len(relationships_df)} relationships") 
        print(f"Loaded {len(communities_df)} communities")
        print(f"Loaded {len(text_units_df)} text units")
        
        # Load graph
        load_graph()
        
        # Load resume data
        load_resume_data()
        
        return True
        
    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_graph():
    """Load the GraphML graph"""
    global graph
    try:
        graph_path = DATA_DIR / "graph.graphml"
        if graph_path.exists():
            graph = nx.read_graphml(str(graph_path))
            print(f"Loaded graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        else:
            print("Graph file not found")
    except Exception as e:
        print(f"Error loading graph: {e}")

def load_resume_data():
    """Load and parse resume data"""
    global resume_data
    try:
        resume_file = INPUT_DIR / "processed-resume-dataset.txt"
        if resume_file.exists():
            with open(resume_file, 'r') as f:
                content = f.read()
            
            # Parse resumes
            resumes = content.split("START OF RESUME")[1:]  # Skip empty first element
            
            for i, resume_text in enumerate(resumes):
                if "END OF RESUME" in resume_text:
                    resume_content = resume_text.split("END OF RESUME")[0].strip()
                    lines = resume_content.split('\n')
                    
                    # Extract name (usually first non-empty line)
                    name = None
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('name:'):
                            name = line
                            break
                    
                    if name:
                        resume_data[f"person_{i+1}"] = {
                            "name": name,
                            "content": resume_content,
                            "id": f"person_{i+1}"
                        }
            
            print(f"Loaded {len(resume_data)} resumes")
        else:
            print("Resume data file not found")
            
    except Exception as e:
        print(f"Error loading resume data: {e}")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        # Load data if not already loaded
        if entities_df is None:
            success = load_data()
            if not success:
                self.send_error(500, "Failed to load data")
                return
        
        if entities_df is None or graph is None:
            self.send_error(500, "Graph data not loaded. Check server logs.")
            return
        
        try:
            # Debug: Print entities info
            print("Entities columns:", entities_df.columns.tolist())
            print("Graph nodes:", len(graph.nodes))
            print("Graph edges:", len(graph.edges))
            
            # Create a mapping from entity title to entity data for type lookup
            entity_map = {}
            for _, entity in entities_df.iterrows():
                title = str(entity.get('title', ''))
                if title:
                    entity_map[title] = {
                        'id': str(entity.get('id', '')),
                        'type': str(entity.get('type', 'other')).lower(),
                        'description': str(entity.get('description', ''))
                    }
            
            # Convert graph nodes to our format, using entities for type information
            nodes = []
            for node_id in graph.nodes():
                # Get type from entities data if available
                entity_info = entity_map.get(node_id, {})
                entity_type = entity_info.get('type', 'other')
                if entity_type == '' or entity_type == 'nan':
                    entity_type = 'other'
                
                # Use entity description if available
                description = entity_info.get('description', '')
                
                node = {
                    "id": node_id,
                    "label": node_id,  # Use the node ID as label (it's already human readable)
                    "type": entity_type,
                    "description": description
                }
                nodes.append(node)
            
            # Convert graph edges to our format
            edges = []
            for source, target in graph.edges():
                # Get edge weight if available
                weight = graph[source][target].get('weight', 0.5)
                
                edge = {
                    "source": source,
                    "target": target,
                    "weight": float(weight),
                    "type": ""  # GraphML doesn't have edge types
                }
                edges.append(edge)
            
            print(f"Created {len(nodes)} nodes and {len(edges)} edges")
            
            # Debug: Print type distribution
            type_counts = {}
            for node in nodes:
                node_type = node['type']
                type_counts[node_type] = type_counts.get(node_type, 0) + 1
            print("Node type distribution:", type_counts)
            
            result = {
                "nodes": nodes,
                "edges": edges,
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            print(f"Graph data error: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Failed to get graph data: {str(e)}")
