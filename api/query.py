import os
import json
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
import pandas as pd
import numpy as np
import networkx as nx
import subprocess
from http.server import BaseHTTPRequestHandler
import urllib.parse

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
        # Load parquet files
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

def query_graphrag(query: str, method: str = "local", root: str = None) -> str:
    if root is None:
        root = Path(__file__).parent.parent / "graphrag-workspace"
    
    query += " Return the response in the form of JSON: [{candidate name: <name>, explanation: <explanation>}]"
    """Query GraphRAG with custom parameters"""
    
    cmd = [
        "graphrag", "query",
        "--root", str(root),
        "--method", method,
        "--query", query
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"GraphRAG error: {result.stderr}")
            return f"Error: {result.stderr}"
            
    except Exception as e:
        return f"Error running query: {str(e)}"

def parse_graphrag_response(raw_response: str) -> str:
    """Parse GraphRAG CLI output to extract the clean answer"""
    
    # Remove timestamp and log prefixes
    lines = raw_response.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip log lines with timestamps and INFO messages
        if re.match(r'^\d{4}-\d{2}-\d{2}', line) or 'INFO' in line:
            continue
        
        # Skip empty lines
        if not line.strip():
            continue
            
        cleaned_lines.append(line.strip())
    
    # Join the remaining content
    clean_response = '\n'.join(cleaned_lines)
    
    # Remove "Global Search Response:" or "Local Search Response:" headers
    clean_response = re.sub(r'^(Global|Local) Search Response:\s*', '', clean_response, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    clean_response = re.sub(r'\n\s*\n', '\n\n', clean_response)
    clean_response = clean_response.strip()
    
    return clean_response

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        # Load data if not already loaded
        if entities_df is None:
            success = load_data()
            if not success:
                self.send_error(500, "Failed to load data")
                return
        
        try:
            # Parse request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            query = request_data.get('q', '')
            top_k = request_data.get('top_k', 8)
            
            print(f"Processing query: {query}")
            
            # Use GraphRAG CLI to get candidates in JSON format
            raw_response = query_graphrag(query, "global")
            clean_response = parse_graphrag_response(raw_response)
            
            print(f"GraphRAG response: {clean_response[:200]}...")
            
            # Try to parse as JSON array first
            try:
                # Look for JSON array in the response - use greedy matching and better boundaries
                # First try to find JSON within code blocks
                code_block_match = re.search(r'```json\s*(\[.*?\])\s*```', clean_response, re.DOTALL)
                if code_block_match:
                    json_str = code_block_match.group(1).strip()
                else:
                    # Fallback: look for JSON array with proper bracket matching
                    json_match = re.search(r'\[.*\]', clean_response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        raise ValueError("No JSON array found in response")
                
                # Clean up the JSON string
                json_str = json_str.strip()
                candidates_json = json.loads(json_str)
                print(f"Successfully parsed {len(candidates_json)} candidates from JSON")
                result = candidates_json[:top_k]
            except Exception as json_error:
                print(f"JSON parsing failed: {json_error}")
                print(f"Raw response for debugging: {clean_response}")
                
                # Fallback: Extract candidates from text and format as JSON
                candidates = []
                lines = clean_response.split('\n')
                current_candidate = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Look for candidate names (often start with numbers or bullet points)
                    name_match = re.match(r'^[\d\.\-\*\•]\s*(.+?)(?:\s*[-:]|$)', line)
                    if name_match:
                        if current_candidate:
                            candidates.append(current_candidate)
                        current_candidate = {
                            "candidate name": name_match.group(1).strip(),
                            "explanation": ""
                        }
                    elif current_candidate and line:
                        # Add to explanation
                        if current_candidate["explanation"]:
                            current_candidate["explanation"] += " "
                        current_candidate["explanation"] += line
                
                # Add the last candidate
                if current_candidate:
                    candidates.append(current_candidate)
                
                # If no candidates found, return the raw response
                if not candidates:
                    candidates = [{
                        "candidate name": "Analysis Result",
                        "explanation": clean_response if clean_response else "No specific candidates found for your query."
                    }]
                
                print(f"Returning {len(candidates)} candidates")
                result = candidates[:top_k]
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            print(f"Query error: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Query failed: {str(e)}")
