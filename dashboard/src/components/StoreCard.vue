<template>
  <div class="store-card">
    <div class="card-header">
      <div class="store-info">
        <h3 class="store-name">{{ store.name }}</h3>
        <span class="store-engine">{{ store.engine }}</span>
      </div>
      <StatusBadge :status="store.status" />
    </div>

    <div class="card-body">
      <div class="info-row">
        <span class="label">Store ID:</span>
        <span class="value">{{ store.id }}</span>
      </div>
      
      <div class="info-row">
        <span class="label">Namespace:</span>
        <span class="value">{{ store.namespace }}</span>
      </div>

      <div class="info-row">
        <span class="label">Admin:</span>
        <span class="value">{{ store.admin_username }} ({{ store.admin_email }})</span>
      </div>

      <div class="info-row">
        <span class="label">Created:</span>
        <span class="value">{{ formatDate(store.created_at) }}</span>
      </div>

      <div class="info-row">
        <span class="label">Last Updated:</span>
        <span class="value">{{ formatDate(store.updated_at) }}</span>
      </div>

      <div v-if="store.store_url" class="info-row">
        <span class="label">URL:</span>
        <a :href="store.store_url" target="_blank" class="store-url">
          {{ store.store_url }}
        </a>
      </div>

      <div v-if="store.failure_reason" class="failure-reason">
        <span class="label">Failure Reason:</span>
        <p class="error-text">{{ store.failure_reason }}</p>
      </div>
    </div>

    <div class="card-actions">
      <button 
        v-if="store.status === 'READY' && store.store_url"
        class="btn btn-primary"
        @click="openStore"
      >
        Open Store
      </button>
      
      <button 
        v-if="canDelete"
        class="btn btn-danger"
        @click="handleDelete"
        :disabled="isDeleting"
      >
        {{ isDeleting ? 'Deleting...' : 'Delete Store' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import StatusBadge from './StatusBadge.vue';

const props = defineProps({
  store: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['delete']);

const isDeleting = computed(() => props.store.status === 'DELETING');

const canDelete = computed(() => {
  return !['DELETED', 'DELETING'].includes(props.store.status);
});

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short'
  });
};

const openStore = () => {
  window.open(props.store.store_url, '_blank');
};

const handleDelete = () => {
  if (confirm(`Are you sure you want to delete store "${props.store.name}"? This action cannot be undone.`)) {
    emit('delete', props.store.id);
  }
};
</script>

<style scoped>
.store-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.store-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f3f4f6;
}

.store-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.store-name {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #111827;
}

.store-engine {
  padding: 4px 8px;
  background-color: #f3f4f6;
  border-radius: 6px;
  font-size: 12px;
  color: #6b7280;
  text-transform: capitalize;
}

.card-body {
  padding: 20px;
}

.info-row {
  display: flex;
  padding: 8px 0;
  font-size: 14px;
}

.label {
  font-weight: 600;
  color: #6b7280;
  min-width: 140px;
}

.value {
  color: #111827;
}

.store-url {
  color: #3b82f6;
  text-decoration: none;
  transition: color 0.2s;
}

.store-url:hover {
  color: #1e40af;
  text-decoration: underline;
}

.failure-reason {
  margin-top: 12px;
  padding: 12px;
  background-color: #fef2f2;
  border-left: 3px solid #ef4444;
  border-radius: 6px;
}

.failure-reason .label {
  display: block;
  margin-bottom: 6px;
  color: #991b1b;
}

.error-text {
  margin: 0;
  color: #991b1b;
  font-size: 13px;
  line-height: 1.5;
}

.card-actions {
  display: flex;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #f3f4f6;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
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
}

.btn-danger {
  background-color: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background-color: #dc2626;
}
</style>
