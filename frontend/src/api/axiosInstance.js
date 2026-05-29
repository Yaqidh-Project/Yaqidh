import axios from 'axios';

// ✅ PRODUCTION-READY: Create configured axios instance with timeouts and retry logic
const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // ✅ 30-second timeout prevents hanging requests
});

// ✅ REQUEST INTERCEPTOR: Inject JWT token + timeout handling
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// ✅ RESPONSE INTERCEPTOR: Handle errors and token refresh
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle timeout errors explicitly
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout - the server took too long to respond');
      return Promise.reject({
        ...error,
        message: 'Request timeout. Please check your connection and try again.',
        status: 408,
      });
    }

    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          // No refresh token available, redirect to login
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
          return Promise.reject(error);
        }

        // Attempt to refresh the token
        const { data } = await axiosInstance.post('/auth/refresh', {
          refresh_token: refreshToken,
        });

        // Update stored tokens
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Log error details for debugging
    if (error.response) {
      console.error(`API Error [${error.response.status}]:`, error.response.data);
    } else if (error.request) {
      console.error('No response from server:', error.request);
    } else {
      console.error('Error setting up request:', error.message);
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;