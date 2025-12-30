import React from 'react';
import './Recommendations.css';

function Recommendations({ recommendations, onInteract, userId }) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="no-recommendations">
        <p>No recommendations available yet. User must have interactions first.</p>
      </div>
    );
  }

  return (
    <div className="recommendations-container">
      <h3>📚 Top Recommendations for {userId}</h3>
      <div className="recommendations-grid">
        {recommendations.map((rec, index) => (
          <div key={rec.content_id} className="recommendation-card">
            <div className="card-rank">#{index + 1}</div>

            <div className="card-content">
              <h4>{rec.title}</h4>
              <p className="category">📁 {rec.category}</p>

              <div className="scores">
                <div className="score-item">
                  <span className="score-label">ML Score:</span>
                  <span className="score-value">
                    {(rec.ml_score * 100).toFixed(1)}%
                  </span>
                  <div className="score-bar">
                    <div
                      className="score-fill ml-score"
                      style={{ width: `${rec.ml_score * 100}%` }}
                    />
                  </div>
                </div>

                {rec.llm_score && (
                  <div className="score-item">
                    <span className="score-label">LLM Score:</span>
                    <span className="score-value">
                      {(rec.llm_score * 100).toFixed(1)}%
                    </span>
                    <div className="score-bar">
                      <div
                        className="score-fill llm-score"
                        style={{ width: `${rec.llm_score * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="score-item combined">
                  <span className="score-label">Combined:</span>
                  <span className="score-value">
                    {(rec.combined_score * 100).toFixed(1)}%
                  </span>
                  <div className="score-bar">
                    <div
                      className="score-fill combined-score"
                      style={{ width: `${rec.combined_score * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="card-actions">
              <button
                className="btn btn-small btn-view"
                onClick={() => onInteract(rec.content_id, 'view')}
              >
                👁️ View
              </button>
              <button
                className="btn btn-small btn-like"
                onClick={() => onInteract(rec.content_id, 'like')}
              >
                👍 Like
              </button>
              <button
                className="btn btn-small btn-save"
                onClick={() => onInteract(rec.content_id, 'save')}
              >
                💾 Save
              </button>
              <button
                className="btn btn-small btn-share"
                onClick={() => onInteract(rec.content_id, 'share')}
              >
                🔗 Share
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Recommendations;
