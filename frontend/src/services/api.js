import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('sh_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const isAuthRequest = error.config.url.includes('/auth/login') || error.config.url.includes('/auth/register');
      if (!isAuthRequest) {
        localStorage.removeItem('sh_token');
        localStorage.removeItem('sh_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Auth
  login: async (credentials) => {
    const res = await apiClient.post('/auth/login', credentials);
    return res.data;
  },
  register: async (userData) => {
    const res = await apiClient.post('/auth/register', userData);
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
  getDoctors: async () => {
    const res = await apiClient.get('/auth/doctors');
    return res.data;
  },

  // Surveys & Predictions
  submitSurvey: async (surveyData) => {
    const res = await apiClient.post('/surveys/', surveyData);
    return res.data;
  },
  getLatestSurvey: async () => {
    const res = await apiClient.get('/surveys/latest');
    return res.data;
  },
  getSurveyHistory: async () => {
    const res = await apiClient.get('/surveys/history');
    return res.data;
  },
  getLatestPrediction: async () => {
    const res = await apiClient.get('/predictions/latest');
    return res.data;
  },
  getPredictionHistory: async () => {
    const res = await apiClient.get('/predictions/history');
    return res.data;
  },
  getPatientPredictions: async (patientId) => {
    const res = await apiClient.get(`/predictions/patient/${patientId}`);
    return res.data;
  },

  // Urgency Triage & Appointments
  bookAppointment: async (appointmentData) => {
    const res = await apiClient.post('/triage/appointments', appointmentData);
    return res.data;
  },
  listAppointments: async () => {
    const res = await apiClient.get('/triage/appointments');
    return res.data;
  },
  updateAppointmentStatus: async (appointmentId, updateData) => {
    const res = await apiClient.patch(`/triage/appointments/${appointmentId}/status`, updateData);
    return res.data;
  },

  // Doctor Clinical Portal
  getTriageQueue: async () => {
    const res = await apiClient.get('/doctor/patients/triage-queue');
    return res.data;
  },
  getPatientDeepDive: async (patientId) => {
    const res = await apiClient.get(`/doctor/patients/${patientId}/deep-dive`);
    return res.data;
  },
  getPopulationInsights: async (params = {}) => {
    const res = await apiClient.get('/doctor/analytics/population', { params });
    return res.data;
  },
  getPopulationTrends: async (params = {}) => {
    const res = await apiClient.get('/doctor/analytics/trends', { params });
    return res.data;
  },

  // Notifications & Alerts
  getNotifications: async (page = 1, pageSize = 20) => {
    const res = await apiClient.get('/notifications', { params: { page, page_size: pageSize } });
    return res.data;
  },
  getUnreadNotificationCount: async () => {
    const res = await apiClient.get('/notifications/unread-count');
    return res.data;
  },
  markNotificationRead: async (id) => {
    const res = await apiClient.patch(`/notifications/${id}/read`);
    return res.data;
  },
  markAllNotificationsRead: async () => {
    const res = await apiClient.post('/notifications/read-all');
    return res.data;
  },

  // Admin Management
  getAdminStats: async () => {
    const res = await apiClient.get('/admin/stats');
    return res.data;
  },
  listAdminUsers: async () => {
    const res = await apiClient.get('/admin/users');
    return res.data;
  },
  updateUserRole: async (userId, role) => {
    const res = await apiClient.patch(`/admin/users/${userId}/role?new_role=${role}`);
    return res.data;
  },
  toggleUserStatus: async (userId) => {
    const res = await apiClient.patch(`/admin/users/${userId}/toggle-status`);
    return res.data;
  },
  createAdminUser: async (userData) => {
    const res = await apiClient.post('/admin/users', userData);
    return res.data;
  },
};

export default api;
