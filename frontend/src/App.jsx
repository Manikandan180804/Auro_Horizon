import React, { useState, useEffect } from 'react';

function App() {
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'Hello! I am Aura, your personalized AI assistant. Tell me about your interests, and I will tailor my recommendations for you.' }
  ]);
  const [input, setInput] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      const res = await fetch('http://localhost:8000/recommendations');
      const data = await res.json();
      setRecommendations(data);
    } catch (err) {
      console.error("Failed to fetch recommendations", err);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history: messages, message: input })
      });
      const data = await res.json();

      setMessages(prev => [...prev, { role: 'ai', content: data.reply }]);
      fetchRecommendations(); // Refresh based on new interests
    } catch (err) {
      console.error("Chat error", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="bg-blob blob-1"></div>
      <div className="bg-blob blob-2"></div>

      {/* Sidebar: Chat */}
      <div className="chat-section glass">
        <div className="chat-header">
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#22d3ee', boxShadow: '0 0 10px #22d3ee' }}></div>
          <h2>Aura</h2>
          <span className="live-tag">REAL-TIME</span>
        </div>
        <div className="chat-history">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
          {loading && <div className="message ai">Processing...</div>}
        </div>
        <div className="chat-input-area">
          <input
            type="text"
            placeholder="Tell Aura your interests..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          />
          <button onClick={handleSend}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>

      {/* Main: Recommendations */}
      <div className="main-section">
        <header className="main-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
            <h1 style={{ margin: 0 }}>Intelligence Stream</h1>
            <div className="stream-status">
              <span className="pulse-dot"></span>
              LIVE DATA
            </div>
          </div>
          <p>Curated 2026 insights based on your evolving landscape</p>
        </header>

        <div className="recommendation-grid">
          {recommendations.map((rec) => (
            <div key={rec.id} className="rect-card glass">
              <img
                src={rec.image_url}
                alt={rec.title}
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = 'https://images.unsplash.com/photo-1618005182384-a33e85e1998a?auto=format&fit=crop&w=800&q=80';
                }}
              />
              <div className="rect-card-content">
                <span className="badge">{rec.category}</span>
                <h3>{rec.title}</h3>
                <p>{rec.description}</p>
                {rec.url && (
                  <a href={rec.url} target="_blank" rel="noopener noreferrer" className="learn-more">
                    Learn More
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="7" y1="17" x2="17" y2="7"></line>
                      <polyline points="7 7 17 7 17 17"></polyline>
                    </svg>
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
