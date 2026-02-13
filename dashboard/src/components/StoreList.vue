<template>
  <div class="store-list-container">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading stores...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <h3>Failed to load stores</h3>
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="$emit('refresh')">
        Try Again
      </button>
    </div>

    <div v-else-if="stores.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <h3>No stores yet</h3>
      <p>Create your first store to get started.</p>
      <button class="btn btn-primary" @click="$emit('create')">
        Create New Store
      </button>
    </div>

    <div v-else class="stores-grid">
      <StoreCard
        v-for="store in stores"
        :key="store.id"
        :store="store"
        @delete="handleDelete"
      />
    </div>
  </div>
</template>

<script setup>
import StoreCard from './StoreCard.vue';

defineProps({
  stores: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  }
});

const emit = defineEmits(['delete', 'refresh', 'create']);

const handleDelete = (storeId) => {
  emit('delete', storeId);
};
</script>

<style scoped>
.store-list-container {
  min-height: 400px;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f4f6;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state p {
  color: #6b7280;
  font-size: 16px;
  margin: 0;
}

.error-icon,
.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.error-state h3,
.empty-state h3 {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.error-state p,
.empty-state p {
  margin: 0 0 24px 0;
  color: #6b7280;
  font-size: 16px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background-color: #1e40af;
}

.stores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
  padding: 20px 0;
}

@media (max-width: 768px) {
  .stores-grid {
    grid-template-columns: 1fr;
  }
}
</style>
