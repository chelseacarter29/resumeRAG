import React, { useState } from 'react'
import VoiceChat from './components/VoiceChat'

type Evidence = { 
  chunk_id: string
  doc_id: string
  section?: string
  text: string 
}

type Candidate = { 
  personId: string
  name: string
  score: number
  why: string
  evidence: Evidence[] 
}

type QueryResponse = { 
  answer: string
  candidates: Candidate[]
  evidence: Evidence[]
}

function App() {
  const [lastResponse, setLastResponse] = useState<QueryResponse | null>(null)
  const [transcript, setTranscript] = useState('')
  const [hasQueried, setHasQueried] = useState(false)
  const [activeTab, setActiveTab] = useState<'find' | 'visualize'>('find')
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [showCandidatesPopup, setShowCandidatesPopup] = useState(false)

  const handleResponse = (data: QueryResponse) => {
    setLastResponse(data)
    if (data.candidates && data.candidates.length > 0) {
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
    "Candidates with Databricks and dbt experience",
    "SQL performance tuning in last 2 years",
    "Python developers with MLOps skills"
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
          <div className="coming-soon">
            <p>Visualization features coming soon...</p>
          </div>
        </section>
      )}

      {activeTab === 'find' && lastResponse && lastResponse.answer && (
        <section className="answer-section">
          <h2>Answer</h2>
          <p className="answer-text">{lastResponse.answer}</p>
          {lastResponse.candidates && lastResponse.candidates.length > 0 && (
            <button 
              className="view-candidates-btn"
              onClick={() => setShowCandidatesPopup(true)}
            >
              View {lastResponse.candidates.length} Candidates
            </button>
          )}
        </section>
      )}

      {/* Candidates Side Popup */}
      {showCandidatesPopup && lastResponse?.candidates && (
        <div className="popup-overlay" onClick={() => setShowCandidatesPopup(false)}>
          <div className="candidates-popup" onClick={(e) => e.stopPropagation()}>
            <div className="popup-header">
              <h2>Candidates ({lastResponse.candidates.length})</h2>
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
                {lastResponse.candidates.map((candidate, idx) => (
                  <div key={`${candidate.personId}-${idx}`} className="candidate-card">
                    <div className="candidate-header">
                      <h3>{candidate.name}</h3>
                      <span className="score">Score: {candidate.score.toFixed(2)}</span>
                    </div>
                    
                    <p className="why-text">{candidate.why}</p>
                    
                    {candidate.evidence && candidate.evidence.length > 0 && (
                      <div className="evidence-snippets">
                        <h4>Evidence</h4>
                        {candidate.evidence.slice(0, 2).map((ev, evidx) => (
                          <div key={`${ev.chunk_id}-${evidx}`} className="evidence-item">
                            <div className="evidence-meta">
                              {ev.section && <span className="section">{ev.section}</span>}
                              <span className="doc-id">{ev.doc_id}</span>
                            </div>
                            <p className="evidence-text">
                              {truncateText(ev.text, 250)}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
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
