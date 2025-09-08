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

  const handleResponse = (data: QueryResponse) => {
    setLastResponse(data)
  }

  const truncateText = (text: string, maxLength: number = 200) => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + '...'
  }

  return (
    <div className="container">
      <header>
        <h1>Voice Query Interface</h1>
      </header>

      <section className="voice-section">
        <VoiceChat 
          endpoint="http://localhost:8000/query" 
          onResponse={handleResponse}
        />
      </section>

      {lastResponse && (
        <>
          {lastResponse.answer && (
            <section className="answer-section">
              <h2>Answer</h2>
              <p className="answer-text">{lastResponse.answer}</p>
            </section>
          )}

          {lastResponse.candidates && lastResponse.candidates.length > 0 && (
            <section className="candidates-section">
              <h2>Candidates</h2>
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
            </section>
          )}

        </>
      )}
    </div>
  )
}

export default App
