<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="closeModal">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h2>Create New Store</h2>
          <button class="close-btn" @click="closeModal" aria-label="Close">
            ×
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="modal-body">
          <div class="form-group">
            <label for="storeName">Store Name *</label>
            <input
              id="storeName"
              v-model="formData.name"
              type="text"
              placeholder="my-awesome-store"
              pattern="^[a-z0-9][a-z0-9-]*[a-z0-9]$"
              minlength="3"
              maxlength="50"
              required
            />
            <small class="help-text">
              Lowercase alphanumeric with hyphens (3-50 chars)
            </small>
          </div>

          <div class="form-group">
            <label for="engine">Engine *</label>
            <select id="engine" v-model="formData.engine" required>
              <option value="">Select an engine</option>
              <option value="woocommerce">WooCommerce</option>
              <option value="medusa" disabled>Medusa (Coming Soon)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="adminUsername">Admin Username *</label>
            <input
              id="adminUsername"
              v-model="formData.admin_username"
              type="text"
              placeholder="admin"
              minlength="3"
              maxlength="50"
              required
            />
          </div>

          <div class="form-group">
            <label for="adminEmail">Admin Email *</label>
            <input
              id="adminEmail"
              v-model="formData.admin_email"
              type="email"
              placeholder="admin@mystore.com"
              required
            />
          </div>

          <div class="form-group">
            <label for="adminPassword">Admin Password *</label>
            <input
              id="adminPassword"
              v-model="formData.admin_password"
              type="password"
              placeholder="At least 8 characters"
              minlength="8"
              required
            />
            <small class="help-text">
              Minimum 8 characters
            </small>
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <div class="modal-footer">
            <button 
              type="button" 
              class="btn btn-secondary" 
              @click="closeModal"
              :disabled="isSubmitting"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              class="btn btn-primary"
              :disabled="isSubmitting"
            >
              {{ isSubmitting ? 'Creating...' : 'Create Store' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['close', 'submit']);

const formData = ref({
  name: '',
  engine: 'woocommerce',
  admin_username: '',
  admin_email: '',
  admin_password: ''
});

const isSubmitting = ref(false);
const error = ref('');

const resetForm = () => {
  formData.value = {
    name: '',
    engine: 'woocommerce',
    admin_username: '',
    admin_email: '',
    admin_password: ''
  };
  error.value = '';
  isSubmitting.value = false;
};

const closeModal = () => {
  if (!isSubmitting.value) {
    resetForm();
    emit('close');
  }
};

const handleSubmit = async () => {
  isSubmitting.value = true;
  error.value = '';

  try {
    await emit('submit', { ...formData.value });
    resetForm();
  } catch (err) {
    error.value = err.message || 'Failed to create store. Please try again.';
    isSubmitting.value = false;
  }
};

watch(() => props.isOpen, (newVal) => {
  if (!newVal) {
    resetForm();
  }
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-container {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #f3f4f6;
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  line-height: 1;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: #f3f4f6;
  color: #111827;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.help-text {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #6b7280;
}

.error-message {
  padding: 12px;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  font-size: 14px;
  margin-bottom: 20px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 20px;
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

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #e5e7eb;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #1e40af;
}
</style>
