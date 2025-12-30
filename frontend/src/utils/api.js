/**
 * Frontend utilities for API communication and error handling
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

/**
 * Handle API errors and return user-friendly messages
 */
export const handleApiError = (error) => {
  if (error.response?.status === 404) {
    return "User not found. Please check the ID and try again.";
  }
  if (error.response?.status === 400) {
    return "Invalid request. Please check your input.";
  }
  if (error.response?.status === 500) {
    return "Server error. Please try again later.";
  }
  return error.message || "An error occurred";
};

/**
 * Retry failed requests with exponential backoff
 */
export const retryRequest = async (fn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise((resolve) => setTimeout(resolve, delay * (2 ** i)));
    }
  }
};

/**
 * Format API response for frontend consumption
 */
export const formatResponse = (data) => {
  return {
    ...data,
    timestamp: new Date(),
    cached: false,
  };
};
