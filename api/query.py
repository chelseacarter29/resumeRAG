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

def query_graphrag(query: str, method: str = "local", root: str = None) -> str:
    """Query GraphRAG data using local search instead of CLI"""
    
    # For Vercel deployment, we'll use local search instead of GraphRAG CLI
    # This is more reliable and doesn't require subprocess calls
    
    try:
        # Simple search through entities and communities
        query_lower = query.lower()
        candidates = []
        
        # Search through entities for person matches
        if entities_df is not None:
            person_entities = entities_df[entities_df['type'] == 'person']
            for _, entity in person_entities.iterrows():
                entity_name = str(entity.get('title', entity.get('name', ''))).lower()
                entity_desc = str(entity.get('description', '')).lower()
                
                # Simple scoring based on text matching
                score = 0
                if query_lower in entity_name:
                    score += 10
                if query_lower in entity_desc:
                    score += 5
                    
                # Check for partial matches
                query_words = query_lower.split()
                for word in query_words:
                    if word in entity_name:
                        score += 3
                    if word in entity_desc:
                        score += 1
                
                if score > 0:
                    candidates.append({
                        "candidate name": entity.get('title', entity.get('name', '')),
                        "explanation": f"Found in entity database with relevance score {score}. {entity.get('description', '')[:200]}..."
                    })
        
        # Search through communities for additional context
        if communities_df is not None:
            for _, community in communities_df.iterrows():
                title = str(community.get('title', '')).lower()
                summary = str(community.get('summary', '')).lower()
                
                if query_lower in title or query_lower in summary:
                    # Extract person names from community content
                    content = str(community.get('full_content', ''))
                    # Simple extraction of person names (this is basic but works)
                    import re
                    person_matches = re.findall(r'([A-Z][a-z]+ [A-Z][a-z]+)', content)
                    for person_name in person_matches[:3]:  # Limit to first 3 matches
                        if not any(c["candidate name"] == person_name for c in candidates):
                            candidates.append({
                                "candidate name": person_name,
                                "explanation": f"Found in community analysis: {summary[:200]}..."
                            })
        
        # If no candidates found, return a helpful message
        if not candidates:
            return json.dumps([{
                "candidate name": "No matches found",
                "explanation": f"No candidates found matching your query: '{query}'. Try different keywords or broader search terms."
            }])
        
        # Sort by relevance and return top candidates
        candidates = candidates[:8]  # Limit to 8 candidates
        return json.dumps(candidates)
        
    except Exception as e:
        return json.dumps([{
            "candidate name": "Search Error",
            "explanation": f"Error processing query: {str(e)}"
        }])

def parse_graphrag_response(raw_response: str) -> str:
    """Parse response - now returns JSON directly"""
    return raw_response

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
            
            # Use local search instead of GraphRAG CLI
            raw_response = query_graphrag(query, "global")
            clean_response = parse_graphrag_response(raw_response)
            
            print(f"Search response: {clean_response[:200]}...")
            
            # Parse the JSON response directly
            try:
                candidates_json = json.loads(clean_response)
                print(f"Successfully parsed {len(candidates_json)} candidates from JSON")
                result = candidates_json[:top_k]
            except Exception as json_error:
                print(f"JSON parsing failed: {json_error}")
                print(f"Raw response for debugging: {clean_response}")
                
                # Fallback response
                result = [{
                    "candidate name": "Search Error",
                    "explanation": f"Error processing query: {json_error}"
                }]
            
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
