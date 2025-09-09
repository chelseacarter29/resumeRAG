# ResumeRAG: Intelligent Resume Search with Graph-Based Knowledge Discovery

## 🎯 Problem Statement

Recruiters often waste time on irrelevant matches or miss strong candidates entirely, resulting in slower hiring and overlooked talent. Traditional resume filtering relies on simple keyword matching, which fails to capture the nuanced relationships between skills, experiences, and roles. This leads to:

- **Poor candidate matching**: Keyword searches miss candidates with relevant but differently-worded experience
- **Overlooked talent**: Strong candidates get filtered out due to rigid search criteria
- **Inefficient screening**: Recruiters spend hours manually reviewing irrelevant resumes
- **Missed connections**: No way to discover candidates with complementary skills or career progression patterns

## 🚀 Our Solution

ResumeRAG tackles the broken resume filtering process by moving beyond traditional keyword search to a graph-based approach using GraphRAG that actually understands relationships between skills, roles, and experiences.

Our solution builds a knowledge graph of resumes using GraphRAG, then lets users query it in natural language to discover and visualize relevant information. We implemented this with Python, GraphRAG, FastAPI, and React, layering LLM-driven context and visualization on top to make resume search more accurate, transparent, and useful.

## ✨ Key Capabilities

### 🧠 Intelligent Natural Language Queries
- **Semantic Understanding**: Ask questions like "Find me candidates with blockchain industry experience" or "Show me someone who transitioned from software to finance"
- **Context-Aware Matching**: Understands relationships between skills, companies, and career progression
- **Flexible Querying**: No need to know exact keywords - describe what you're looking for in plain English

### 📊 Interactive Knowledge Graph Visualization
- **Visual Network**: See how candidates, skills, companies, and technologies connect
- **Depth Control**: Expand your search by 1-5 degrees of separation to find related candidates
- **Real-time Filtering**: Search and filter the graph to focus on specific areas of interest
- **Relationship Discovery**: Uncover unexpected connections between candidates and opportunities

### 🎯 Advanced Candidate Discovery
- **Career Progression Analysis**: Find candidates who've successfully transitioned between roles or industries
- **Skill Combination Matching**: Discover candidates with unique combinations of technical and soft skills
- **Company Experience Mapping**: Identify candidates with experience at specific companies or in particular industries
- **Interdisciplinary Talent**: Find candidates with diverse backgrounds and cross-functional experience

### 🔍 Smart Search Features
- **Example Queries**: Pre-built queries for common recruitment scenarios:
  - "Find me a candidate who has blockchain industry experience"
  - "Show me a candidate with a strong fullstack builder profile"
  - "Show me some candidates with strong interdisciplinary experience"
- **Voice Input**: Speak your queries naturally using the built-in voice interface
- **Real-time Results**: Get instant, ranked candidate matches with detailed explanations

## 🏗️ Technical Architecture

### Backend (Python + FastAPI)
- **GraphRAG Integration**: Processes resume data into a knowledge graph with entities and relationships
- **OpenAI API**: Powers natural language understanding and query processing
- **FastAPI Server**: Provides RESTful API endpoints for frontend communication
- **Graph Database**: Stores and queries the resume knowledge graph efficiently

### Frontend (React + TypeScript)
- **Interactive UI**: Clean, modern interface for querying and visualizing results
- **Graph Visualization**: D3.js-powered network visualization with zoom, pan, and filtering
- **Voice Interface**: Speech-to-text integration for natural query input
- **Real-time Updates**: Live search results and graph updates

### Data Processing Pipeline
1. **Resume Ingestion**: Parse and structure resume data from various formats
2. **Entity Extraction**: Identify people, companies, skills, technologies, and experiences
3. **Relationship Mapping**: Build connections between entities using GraphRAG
4. **Knowledge Graph Construction**: Create a queryable graph database
5. **LLM Enhancement**: Add semantic understanding and context to the graph

## 🚀 Getting Started

### Prerequisites
- **Python 3.9+**
- **Node.js 18+**
- **OpenAI API Key** (for GraphRAG processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yaoderek/resumeRAG.git
   cd resumeRAG
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file in graphrag-workspace directory
   echo "OPENAI_API_KEY=your_openai_api_key_here" > graphrag-workspace/.env
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   python3 backend/app.py
   ```
   The API will be available at `http://localhost:8000`

2. **Start the frontend development server** (in a new terminal)
   ```bash
   npm run dev
   ```
   The application will be available at `http://localhost:5173`

3. **Access the application**
   - Open your browser to `http://localhost:5173`
   - Start querying resumes using natural language!

### API Endpoints

- `GET /health` - Health check endpoint
- `POST /query` - Submit natural language queries
- `GET /graph-data` - Retrieve the knowledge graph data
- `GET /docs` - Interactive API documentation

## 📝 Usage Examples

### Basic Queries
```
"Find me Python developers with MLOps experience"
"Who has worked at both startups and big tech companies?"
"Show me candidates with finance and technology backgrounds"
```

### Advanced Discovery
```
"Find someone who transitioned from engineering to product management"
"Who has experience with both frontend and backend technologies?"
"Show me candidates with strong leadership and technical skills"
```

### Graph Exploration
- Use the **Visualization** tab to explore the knowledge graph
- Search for specific nodes (people, companies, skills)
- Adjust the depth slider to expand your search radius
- Click on nodes to see detailed information

## 🔧 Configuration

### GraphRAG Settings
The GraphRAG configuration is located in `graphrag-workspace/config.yaml`. Key settings include:
- **LLM Model**: Configure which OpenAI model to use
- **Entity Types**: Define what types of entities to extract
- **Relationship Types**: Specify how entities should be connected

### Frontend Customization
- **Example Queries**: Modify the example queries in `src/App.tsx`
- **Styling**: Customize the UI in `src/index.css`
- **API Endpoints**: Update API URLs in the component files if needed

## 📊 Data Format

The system expects resume data in a structured format. The current implementation processes:
- **Candidate Information**: Names, contact details, education
- **Work Experience**: Companies, roles, responsibilities, dates
- **Skills**: Technical skills, programming languages, tools
- **Projects**: Project descriptions, technologies used, outcomes

## 🤝 Contributing

We welcome contributions! Please feel free to:
- Report bugs or issues
- Suggest new features
- Submit pull requests
- Improve documentation

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **GraphRAG**: Microsoft's framework for building knowledge graphs from unstructured text
- **OpenAI**: For providing the LLM capabilities that power our natural language understanding
- **FastAPI**: For the robust and fast API framework
- **React**: For the modern, interactive frontend framework

---

**ResumeRAG** - Making resume search intelligent, visual, and efficient. 🚀
