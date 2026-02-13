<template>
  <div id="app">
    <header class="app-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="app-title">
            <span class="logo-icon">🏪</span>
            Store Provisioning Platform
          </h1>
          <div 
            class="health-indicator" 
            :class="{ 'health-online': isHealthy, 'health-offline': !isHealthy }"
            :title="isHealthy ? 'API is healthy' : 'API is offline'"
          >
            <span class="health-dot"></span>
            {{ isHealthy ? 'Online' : 'Offline' }}
          </div>
        </div>
        <button 
          class="btn btn-primary create-btn" 
          @click="openCreateModal"
          :disabled="!isHealthy"
        >
          + Create New Store
        </button>
      </div>
    </header>

    <main class="app-main">
      <div class="container">
        <div class="main-header">
          <h2>Your Stores</h2>
          <button 
            class="btn btn-secondary refresh-btn" 
            @click="fetchStores"
            :disabled="loading"
          >
            🔄 Refresh
          </button>
        </div>

        <StoreList
          :stores="stores"
          :loading="loading"
          :error="errorMessage"
          @delete="deleteStore"
          @refresh="fetchStores"
          @create="openCreateModal"
        />
      </div>
    </main>

    <CreateStoreModal
      :is-open="isCreateModalOpen"
      @close="closeCreateModal"
      @submit="createStore"
    />

    <div v-if="notification" class="notification" :class="`notification-${notification.type}`">
      {{ notification.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import StoreList from './components/StoreList.vue';
import CreateStoreModal from './components/CreateStoreModal.vue';
import storeApi from './api/storeApi';

// State
const stores = ref([]);
const loading = ref(false);
const errorMessage = ref(null);
const isHealthy = ref(true);
const isCreateModalOpen = ref(false);
const notification = ref(null);
let pollingInterval = null;

// Health check
const checkHealth = async () => {
  try {
    await storeApi.getHealth();
    isHealthy.value = true;
  } catch (error) {
    console.error('Health check failed:', error);
    isHealthy.value = false;
  }
};

// Fetch stores
const fetchStores = async () => {
  loading.value = true;
  errorMessage.value = null;
  
  try {
    const data = await storeApi.listStores();
    stores.value = data;
  } catch (error) {
    console.error('Failed to fetch stores:', error);
    errorMessage.value = error.response?.data?.message || error.message || 'Failed to load stores';
  } finally {
    loading.value = false;
  }
};

// Create store
const createStore = async (storeData) => {
  try {
    const newStore = await storeApi.createStore(storeData);
    stores.value.unshift(newStore);
    closeCreateModal();
    showNotification('Store creation initiated! Status: PROVISIONING', 'success');
  } catch (error) {
    console.error('Failed to create store:', error);
    const errorMsg = error.response?.data?.message || error.message || 'Failed to create store';
    showNotification(errorMsg, 'error');
    throw new Error(errorMsg);
  }
};

// Delete store
const deleteStore = async (storeId) => {
  try {
    await storeApi.deleteStore(storeId);
    
    // Update the store status in the list
    const storeIndex = stores.value.findIndex(s => s.id === storeId);
    if (storeIndex !== -1) {
      stores.value[storeIndex].status = 'DELETED';
    }
    
    showNotification('Store deleted successfully', 'success');
    
    // Refresh the list after a short delay
    setTimeout(() => {
      fetchStores();
    }, 1000);
  } catch (error) {
    console.error('Failed to delete store:', error);
    const errorMsg = error.response?.data?.message || error.message || 'Failed to delete store';
    showNotification(errorMsg, 'error');
  }
};

// Modal controls
const openCreateModal = () => {
  isCreateModalOpen.value = true;
};

const closeCreateModal = () => {
  isCreateModalOpen.value = false;
};

// Notification system
const showNotification = (message, type = 'info') => {
  notification.value = { message, type };
  setTimeout(() => {
    notification.value = null;
  }, 5000);
};

// Start polling for store status updates
const startPolling = () => {
  pollingInterval = setInterval(() => {
    // Only poll if there are stores in non-final states
    const hasActiveStores = stores.value.some(
      store => ['PROVISIONING', 'DELETING'].includes(store.status)
    );
    
    if (hasActiveStores) {
      fetchStores();
    }
  }, 5000); // Poll every 5 seconds
};

// Stop polling
const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
};

// Lifecycle hooks
onMounted(async () => {
  await checkHealth();
  if (isHealthy.value) {
    await fetchStores();
  }
  startPolling();
  
  // Also check health periodically
  setInterval(checkHealth, 30000); // Every 30 seconds
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f9fafb;
  color: #111827;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 20px 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.app-title {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
}

.logo-icon {
  font-size: 28px;
}

.health-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.health-online {
  background-color: #d1fae5;
  color: #065f46;
}

.health-offline {
  background-color: #fee2e2;
  color: #991b1b;
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.health-online .health-dot {
  background-color: #10b981;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.health-offline .health-dot {
  background-color: #ef4444;
}

.create-btn {
  font-size: 16px;
  padding: 12px 24px;
}

.app-main {
  flex: 1;
  padding: 32px 0;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 32px;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.main-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #1e40af;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #e5e7eb;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 16px 24px;
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  animation: slideIn 0.3s ease-out;
  z-index: 1001;
  max-width: 400px;
}

.notification-success {
  background-color: #d1fae5;
  color: #065f46;
}

.notification-error {
  background-color: #fee2e2;
  color: #991b1b;
}

.notification-info {
  background-color: #dbeafe;
  color: #1e40af;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .main-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .container {
    padding: 0 16px;
  }

  .app-main {
    padding: 24px 0;
  }
}
</style>
