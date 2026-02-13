import axios from 'axios';

const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const storeApi = {
  /**
   * Get health status of the API
   */
  async getHealth() {
    const response = await apiClient.get('/health');
    return response.data;
  },

  /**
   * Get all stores
   */
  async listStores() {
    const response = await apiClient.get('/stores');
    return response.data.stores;
  },

  /**
   * Get a specific store by ID
   */
  async getStore(storeId) {
    const response = await apiClient.get(`/stores/${storeId}`);
    return response.data;
  },

  /**
   * Create a new store
   */
  async createStore(storeData) {
    const response = await apiClient.post('/stores', storeData);
    return response.data;
  },

  /**
   * Delete a store by ID
   */
  async deleteStore(storeId) {
    const response = await apiClient.delete(`/stores/${storeId}`);
    return response.data;
  },
};

export default storeApi;
