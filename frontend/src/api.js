/**
 * Context IQ Frontend API Client
 * Handles all communication with the backend API
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = {
  /**
   * Check API health status
   */
  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) throw new Error('Health check failed');
      return await response.json();
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  },

  /**
   * Get personalized recommendations for a user
   */
  async getRecommendations(userId, limit = 10) {
    try {
      const url = new URL(`${API_BASE_URL}/recommendations`);
      url.searchParams.append('user_id', userId);
      url.searchParams.append('limit', limit);

      const response = await fetch(url.toString());
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('User not found or no recommendations available');
        }
        throw new Error('Failed to fetch recommendations');
      }
      return await response.json();
    } catch (error) {
      console.error('Get recommendations error:', error);
      throw error;
    }
  },

  /**
   * Log a user interaction with content
   */
  async logInteraction(userId, contentId, interactionType, durationSeconds = 0, metadata = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/interact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          content_id: contentId,
          interaction_type: interactionType,
          duration_seconds: durationSeconds,
          metadata: metadata,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to log interaction');
      }

      return await response.json();
    } catch (error) {
      console.error('Log interaction error:', error);
      throw error;
    }
  },

  /**
   * Get user profile and statistics
   */
  async getUserProfile(userId) {
    try {
      const response = await fetch(`${API_BASE_URL}/user-profile/${userId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch user profile');
      }
      return await response.json();
    } catch (error) {
      console.error('Get user profile error:', error);
      throw error;
    }
  },

  /**
   * List all available content
   */
  async listContent(category = null, limit = 50) {
    try {
      const url = new URL(`${API_BASE_URL}/content`);
      if (category) url.searchParams.append('category', category);
      url.searchParams.append('limit', limit);

      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error('Failed to list content');
      }
      return await response.json();
    } catch (error) {
      console.error('List content error:', error);
      throw error;
    }
  },
};

export default api;
