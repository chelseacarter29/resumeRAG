import React, { useState } from 'react'
import VoiceChat from './components/VoiceChat'
import GraphVisualization from './components/GraphVisualization'

// New simplified response format
type CandidateResult = {
  "candidate name": string
  explanation: string
}

// For backward compatibility and internal state
type Candidate = { 
  name: string
  explanation: string
}

type QueryResponse = CandidateResult[] | { candidates?: CandidateResult[] }

function App() {
  const [lastResponse, setLastResponse] = useState<CandidateResult[] | null>(null)
  const [transcript, setTranscript] = useState('')
  const [hasQueried, setHasQueried] = useState(false)
  const [activeTab, setActiveTab] = useState<'find' | 'visualize'>('find')
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [showCandidatesPopup, setShowCandidatesPopup] = useState(false)

  const handleResponse = (data: any) => {
    // Handle new JSON array format
    let candidates: CandidateResult[] = []
    
    if (Array.isArray(data)) {
      candidates = data
    } else if (data.candidates && Array.isArray(data.candidates)) {
      candidates = data.candidates
    }
    
    setLastResponse(candidates)
    if (candidates.length > 0) {
      setShowCandidatesPopup(true)
    }
  }

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode)
  }

  // Apply dark mode to body element
  React.useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
    }
  }, [isDarkMode])

  const handleSend = () => {
    setHasQueried(true)
  }

  const resetInterface = () => {
    setLastResponse(null)
    setTranscript('')
    setHasQueried(false)
    setShowCandidatesPopup(false)
  }

  const exampleQueries = [
    "Find me a candidate who has blockchain industry experience",
    "Show me a candidate with a strong fullstack builder profile",
    "Show me some candidates with strong interdisciplinary experience"
  ]

  const handleExampleClick = (query: string) => {
    setTranscript(query)
  }

  const truncateText = (text: string, maxLength: number = 200) => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + '...'
  }

  return (
    <div className={`container ${isDarkMode ? 'dark-mode' : ''}`}>
      <header>
        <div className="header-controls">
          <button 
            className="dark-mode-toggle"
            onClick={toggleDarkMode}
            aria-label="Toggle dark mode"
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
        </div>
        <h1>RESUME RAG</h1>
        <p className="description">
          Search through resumes using natural language. Ask about skills, experience, companies, or any combination.
        </p>
        
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'find' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('find')
              resetInterface()
            }}
          >
            Find Candidates
          </button>
          <button 
            className={`tab ${activeTab === 'visualize' ? 'active' : ''}`}
            onClick={() => setActiveTab('visualize')}
          >
            Visualize
          </button>
        </div>
      </header>

      {activeTab === 'find' && (
        <section className="voice-section">
          <VoiceChat 
            endpoint="http://localhost:8000/query" 
            onResponse={handleResponse}
            transcript={transcript}
            setTranscript={setTranscript}
            onSend={handleSend}
          />
          
          {!hasQueried && (
            <div className="example-queries">
              <p className="example-label">Try these examples:</p>
              <div className="example-buttons">
                {exampleQueries.map((query, idx) => (
                  <button 
                    key={idx}
                    className="example-button"
                    onClick={() => handleExampleClick(query)}
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
      
      {activeTab === 'visualize' && (
        <section className="visualize-section">
          <GraphVisualization />
        </section>
      )}

      {activeTab === 'find' && lastResponse && lastResponse.length > 0 && (
        <section className="answer-section">
          <h2>Search Results</h2>
          <p className="answer-text">Found {lastResponse.length} matching candidates</p>
          <button 
            className="view-candidates-btn"
            onClick={() => setShowCandidatesPopup(true)}
          >
            View {lastResponse.length} Candidates
          </button>
        </section>
      )}

      {/* Candidates Side Popup */}
      {showCandidatesPopup && lastResponse && lastResponse.length > 0 && (
        <div className="popup-overlay" onClick={() => setShowCandidatesPopup(false)}>
          <div className="candidates-popup" onClick={(e) => e.stopPropagation()}>
            <div className="popup-header">
              <h2>Candidates ({lastResponse.length})</h2>
              <button 
                className="close-popup"
                onClick={() => setShowCandidatesPopup(false)}
                aria-label="Close candidates popup"
              >
                ✕
              </button>
            </div>
            
            <div className="popup-content">
              <div className="candidates-list">
                {lastResponse.map((candidate, idx) => (
                  <div key={`${candidate["candidate name"]}-${idx}`} className="candidate-card">
                    <div className="candidate-header">
                      <h3>{candidate["candidate name"]}</h3>
                      <span className="match-indicator">✓ Match</span>
                    </div>
                    
                    <div className="explanation-section">
                      <h4>Why this candidate matches:</h4>
                      <p className="explanation-text">{candidate.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
