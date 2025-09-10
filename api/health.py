import os
import json
from pathlib import Path
import pandas as pd
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
        
        try:
            result = {
                "status": "healthy",
                "entities_loaded": entities_df is not None,
                "relationships_loaded": relationships_df is not None,
                "communities_loaded": communities_df is not None,
                "text_units_loaded": text_units_df is not None,
                "graph_loaded": graph is not None,
                "resumes_loaded": len(resume_data) > 0
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            print(f"Health check error: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Health check failed: {str(e)}")
