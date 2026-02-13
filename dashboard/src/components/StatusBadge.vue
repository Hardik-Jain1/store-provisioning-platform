<template>
  <span 
    class="status-badge" 
    :class="`status-${status.toLowerCase()}`"
  >
    <span class="status-dot"></span>
    {{ status }}
  </span>
</template>

<script setup>
defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['PROVISIONING', 'READY', 'FAILED', 'DELETING', 'DELETED'].includes(value)
  }
});
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-provisioning {
  background-color: #dbeafe;
  color: #1e40af;
}

.status-provisioning .status-dot {
  background-color: #3b82f6;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.status-ready {
  background-color: #d1fae5;
  color: #065f46;
}

.status-ready .status-dot {
  background-color: #10b981;
}

.status-failed {
  background-color: #fee2e2;
  color: #991b1b;
}

.status-failed .status-dot {
  background-color: #ef4444;
}

.status-deleting {
  background-color: #fed7aa;
  color: #92400e;
}

.status-deleting .status-dot {
  background-color: #f59e0b;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.status-deleted {
  background-color: #f3f4f6;
  color: #6b7280;
}

.status-deleted .status-dot {
  background-color: #9ca3af;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
