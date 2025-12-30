import React, { useState, useEffect } from 'react';
import './App.css';
import Recommendations from './components/Recommendations';
import api from './api';

function App() {
  const [userId, setUserId] = useState('');
  const [userIdInput, setUserIdInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    // Check API health on load
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const data = await api.checkHealth();
      setHealth(data);
    } catch (err) {
      console.error('Health check failed:', err);
    }
  };

  const handleSetUser = (e) => {
    e.preventDefault();
    if (userIdInput.trim()) {
      setUserId(userIdInput);
      setError('');
    }
  };

  const handleGetRecommendations = async () => {
    if (!userId) {
      setError('Please enter a user ID');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const data = await api.getRecommendations(userId);
      setRecommendations(data.recommendations);
    } catch (err) {
      setError(err.message || 'Failed to fetch recommendations');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInteract = async (contentId, type) => {
    try {
      await api.logInteraction(userId, contentId, type, 0, {});
      alert(`${type} interaction logged!`);
      // Refresh recommendations after interaction
      setTimeout(handleGetRecommendations, 1000);
    } catch (err) {
      setError(err.message || 'Failed to log interaction');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎯 Context IQ</h1>
        <p>Personalized Content Recommendation System</p>
      </header>

      <main className="container">
        {/* Health Status */}
        {health && (
          <div className={`health-status ${health.status}`}>
            <p>
              <strong>API Status:</strong> {health.status.toUpperCase()}
            </p>
            <div className="services">
              {Object.entries(health.services).map(([service, status]) => (
                <span key={service} className={`service ${status ? 'up' : 'down'}`}>
                  {service}: {status ? '✓' : '✗'}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* User Input */}
        <section className="user-input-section">
          <h2>1. Identify User</h2>
          <form onSubmit={handleSetUser} className="user-form">
            <input
              type="text"
              value={userIdInput}
              onChange={(e) => setUserIdInput(e.target.value)}
              placeholder="Enter user ID (e.g., user123)"
              className="input-field"
            />
            <button type="submit" className="btn btn-primary">
              Set User
            </button>
          </form>
          {userId && (
            <p className="current-user">
              Current user: <strong>{userId}</strong>
            </p>
          )}
        </section>

        {/* Recommendations */}
        <section className="recommendations-section">
          <h2>2. Get Recommendations</h2>
          <button
            onClick={handleGetRecommendations}
            disabled={!userId || loading}
            className="btn btn-success"
          >
            {loading ? 'Loading...' : 'Fetch Recommendations'}
          </button>

          {error && <div className="error-message">{error}</div>}

          {recommendations.length > 0 && (
            <Recommendations
              recommendations={recommendations}
              onInteract={handleInteract}
              userId={userId}
            />
          )}
        </section>
      </main>

      <footer className="App-footer">
        <p>Context IQ © 2024 | ML-powered recommendations with AWS Bedrock integration</p>
      </footer>
    </div>
  );
}

export default App;
