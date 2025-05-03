import axios from 'axios';

// Base URL for API requests - use relative URL for proxy to work correctly
const API_URL = '/api';

// Create axios instance with consistent configuration
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Upload a document
export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    // Use the api instance with modified headers for form data
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    console.log('Upload response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Upload error:', error);
    throw handleApiError(error);
  }
};

// Process a document
export const processDocument = async (documentId) => {
  try {
    console.log(`Processing document with ID: ${documentId}`);
    
    // Use the api instance with the correct relative URL
    const response = await api.post(`/documents/${documentId}/process`, {});
    
    console.log('Process response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Process error details:', error);
    
    if (error.response) {
      console.error('Error response data:', error.response.data);
      console.error('Error response status:', error.response.status);
    }
    
    throw handleApiError(error);
  }
};

// Fetch a document
export const fetchDocument = async (documentId, includeText = false) => {
  try {
    const response = await api.get(`/documents/${documentId}?include_text=${includeText}`);
    return response.data;
  } catch (error) {
    console.error('Fetch document error:', error);
    throw handleApiError(error);
  }
};

// Fetch all documents
export const fetchDocuments = async () => {
  try {
    const response = await api.get('/documents');
    return response.data;
  } catch (error) {
    console.error('Fetch documents error:', error);
    throw handleApiError(error);
  }
};

// Delete a document
export const deleteDocument = async (documentId) => {
  try {
    const response = await api.delete(`/documents/${documentId}`);
    return response.data;
  } catch (error) {
    console.error('Delete error:', error);
    throw handleApiError(error);
  }
};

// Check memory status (for debugging)
export const checkMemoryStatus = async () => {
  try {
    const response = await api.get('/memory-status');
    console.log('Memory status response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Memory status error:', error);
    throw handleApiError(error);
  }
};

// Helper function to handle API errors
const handleApiError = (error) => {
  if (error.response) {
    // The request was made and the server responded with a status code
    // that falls out of the range of 2xx
    console.error('API error response:', error.response);
    return new Error(error.response.data.detail || 'Server error');
  } else if (error.request) {
    // The request was made but no response was received
    console.error('No response received:', error.request);
    return new Error('No response from server. Please check your connection.');
  } else {
    // Something happened in setting up the request that triggered an Error
    return new Error('Error setting up request: ' + error.message);
  }
};

export default api;
