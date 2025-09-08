import os
import json
import re
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import networkx as nx
from xml.etree import ElementTree as ET

app = FastAPI(title="Resume RAG API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryFilters(BaseModel):
    must_skills: List[str] = []
    should_skills: List[str] = []
    since_year: int = 2020

class QueryRequest(BaseModel):
    q: str
    top_k: int = 8
    mode: str = "auto"  # "local", "global", or "auto"
    filters: QueryFilters = QueryFilters()

class Evidence(BaseModel):
    chunk_id: str
    doc_id: str
    section: Optional[str] = None
    text: str

class Candidate(BaseModel):
    personId: str
    name: str
    score: float
    why: str
    evidence: List[Evidence]

class QueryResponse(BaseModel):
    answer: str
    candidates: List[Candidate] = []
    evidence: List[Evidence] = []

# Global variables for data
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

def search_entities(query: str, top_k: int = 10) -> List[Dict]:
    """Search entities based on query"""
    if entities_df is None:
        return []
    
    query_lower = query.lower()
    results = []
    
    for _, entity in entities_df.iterrows():
        score = 0
        entity_name = str(entity.get('title', entity.get('name', ''))).lower()
        entity_desc = str(entity.get('description', '')).lower()
        
        # Simple scoring based on text matching
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
            results.append({
                'entity': entity,
                'score': score,
                'name': entity.get('title', entity.get('name', '')),
                'description': entity.get('description', '')
            })
    
    # Sort by score and return top results
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]

def search_communities(query: str, top_k: int = 5) -> List[Dict]:
    """Search community reports based on query"""
    if communities_df is None:
        return []
    
    query_lower = query.lower()
    results = []
    
    for _, community in communities_df.iterrows():
        score = 0
        title = str(community.get('title', '')).lower()
        summary = str(community.get('summary', '')).lower()
        full_content = str(community.get('full_content', '')).lower()
        
        # Simple scoring
        if query_lower in title:
            score += 15
        if query_lower in summary:
            score += 10
        if query_lower in full_content:
            score += 5
            
        # Check for partial matches
        query_words = query_lower.split()
        for word in query_words:
            if word in title:
                score += 5
            if word in summary:
                score += 3
            if word in full_content:
                score += 1
        
        if score > 0:
            results.append({
                'community': community,
                'score': score,
                'title': community.get('title', ''),
                'summary': community.get('summary', ''),
                'full_content': community.get('full_content', '')
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]

def extract_person_candidates(query: str, entity_results: List[Dict], top_k: int = 8) -> List[Candidate]:
    """Extract person candidates from search results"""
    candidates = []
    
    # Get person entities
    person_entities = [r for r in entity_results if 'person' in str(r.get('name', '')).lower()]
    
    # Also search resume data directly
    query_lower = query.lower()
    for person_id, person_data in resume_data.items():
        name = person_data['name']
        content = person_data['content'].lower()
        
        score = 0
        why_parts = []
        
        # Score based on content matching
        if query_lower in content:
            score += 10
            why_parts.append("Query terms found in resume")
        
        # Check for specific skills/technologies
        query_words = query_lower.split()
        found_skills = []
        for word in query_words:
            if word in content:
                score += 2
                found_skills.append(word)
        
        if found_skills:
            why_parts.append(f"Skills match: {', '.join(found_skills)}")
        
        if score > 0:
            # Create evidence from resume content
            evidence = [Evidence(
                chunk_id=f"resume_{person_id}",
                doc_id=person_id,
                section="Resume",
                text=person_data['content'][:500] + "..." if len(person_data['content']) > 500 else person_data['content']
            )]
            
            candidates.append(Candidate(
                personId=person_id,
                name=name,
                score=min(score / 10.0, 1.0),  # Normalize score
                why="; ".join(why_parts) if why_parts else f"Relevant to query: {query}",
                evidence=evidence
            ))
    
    # Sort by score and return top candidates
    candidates.sort(key=lambda x: x.score, reverse=True)
    return candidates[:top_k]

def generate_answer(query: str, entity_results: List[Dict], community_results: List[Dict]) -> str:
    """Generate answer based on search results"""
    
    if not entity_results and not community_results:
        return "I couldn't find specific information related to your query in the resume database."
    
    answer_parts = []
    
    # Add community insights if available
    if community_results:
        top_community = community_results[0]
        summary = top_community.get('summary', '')
        if summary:
            answer_parts.append(f"Based on the resume analysis: {summary}")
    
    # Add entity information
    if entity_results:
        relevant_entities = entity_results[:3]  # Top 3 entities
        entity_names = [r['name'] for r in relevant_entities if r['name']]
        if entity_names:
            answer_parts.append(f"Key relevant entities found: {', '.join(entity_names)}")
    
    # Default answer if we have results but no specific content
    if not answer_parts:
        if entity_results:
            answer_parts.append(f"Found {len(entity_results)} relevant entities related to your query.")
        if community_results:
            answer_parts.append(f"Found information in {len(community_results)} related resume clusters.")
    
    return " ".join(answer_parts) if answer_parts else "Results found but no detailed information available."

@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    success = load_data()
    if not success:
        print("WARNING: Failed to load some data. Functionality may be limited.")

@app.get("/")
async def root():
    return {"message": "Resume RAG API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "entities_loaded": entities_df is not None,
        "relationships_loaded": relationships_df is not None,
        "communities_loaded": communities_df is not None,
        "text_units_loaded": text_units_df is not None,
        "graph_loaded": graph is not None,
        "resumes_loaded": len(resume_data) > 0
    }

@app.post("/query", response_model=QueryResponse)
async def query_resumes(request: QueryRequest):
    """Query the resume database"""
    
    if entities_df is None:
        raise HTTPException(
            status_code=500, 
            detail="Data not loaded. Check server logs."
        )
    
    try:
        print(f"Processing query: {request.q}")
        
        # Search entities and communities
        entity_results = search_entities(request.q, top_k=20)
        community_results = search_communities(request.q, top_k=10)
        
        print(f"Found {len(entity_results)} entity results, {len(community_results)} community results")
        
        # Generate answer
        answer = generate_answer(request.q, entity_results, community_results)
        
        # Extract candidates
        candidates = extract_person_candidates(request.q, entity_results, request.top_k)
        
        print(f"Generated answer and {len(candidates)} candidates")
        
        return QueryResponse(
            answer=answer,
            candidates=candidates,
            evidence=[]
        )
        
    except Exception as e:
        print(f"Query error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)