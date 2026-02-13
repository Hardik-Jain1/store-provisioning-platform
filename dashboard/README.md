# Store Provisioning Platform - Dashboard

A modern, production-ready Vue 3 dashboard for managing ecommerce store provisioning on Kubernetes.

## Features

- **Store Management**: Create, view, and delete stores
- **Real-time Status Updates**: Automatic polling for store status changes
- **Status Visualization**: Color-coded badges for different store states
  - 🔵 PROVISIONING - Store is being deployed
  - 🟢 READY - Store is operational
  - 🔴 FAILED - Provisioning failed
  - 🟠 DELETING - Store is being removed
  - ⚪ DELETED - Store has been removed

## 🛠️ Tech Stack

- **Vue 3** - Composition API for reactive state management
- **Vite** - Fast build tool and dev server
- **Axios** - HTTP client for API communication
- **Modern CSS** - Clean, custom styling without heavy frameworks

## 📋 Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:5000` (see backend README)

## 🏃 Quick Start

### 1. Install Dependencies

```bash
cd dashboard
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### 3. Build for Production

```bash
npm run build
```

The optimized production build will be in the `dist/` directory.

### 4. Preview Production Build

```bash
npm run preview
```

## 🎯 Usage Guide

### Creating a Store

1. Click the **"+ Create New Store"** button in the header
2. Fill in the form:
   - **Store Name**: Lowercase alphanumeric with hyphens (e.g., `my-awesome-store`)
   - **Engine**: Select WooCommerce (Medusa coming soon)
   - **Admin Username**: Username for store admin access
   - **Admin Email**: Email for store admin
   - **Admin Password**: Minimum 8 characters
3. Click **"Create Store"**
4. The store will appear in the list with status `PROVISIONING`
5. Status will automatically update to `READY` when provisioning completes

### Viewing Stores

- All stores are displayed as cards in a responsive grid
- Each card shows:
  - Store name and engine
  - Current status badge
  - Store ID and namespace
  - Admin credentials
  - Creation timestamp
  - Store URL (when ready)
  - Failure reason (if failed)

### Opening a Store

- Click the **"Open Store"** button on any `READY` store
- The store will open in a new browser tab

### Deleting a Store

1. Click the **"Delete Store"** button on any store card
2. Confirm the deletion in the dialog
3. The store status will change to `DELETED`
4. All Kubernetes resources will be cleaned up

### Refreshing Store List

- Click the **"🔄 Refresh"** button to manually refresh the store list
- The dashboard automatically polls for updates every 5 seconds when there are stores in `PROVISIONING` or `DELETING` states

## 📁 Project Structure

```
dashboard/
├── src/
│   ├── api/
│   │   └── storeApi.js          # API client for backend communication
│   ├── components/
│   │   ├── CreateStoreModal.vue # Store creation modal
│   │   ├── StatusBadge.vue      # Status badge component
│   │   ├── StoreCard.vue        # Individual store card
│   │   └── StoreList.vue        # Store list container
│   ├── App.vue                  # Main application component
│   ├── main.js                  # Application entry point
│   └── style.css                # Global styles
├── index.html
├── package.json
├── vite.config.js              # Vite configuration with proxy
└── README.md
```

## 🔌 API Integration

The dashboard communicates with the backend API defined in `api-spec.yaml`:

### Endpoints Used

- `GET /api/v1/health` - Health check
- `GET /api/v1/stores` - List all stores
- `POST /api/v1/stores` - Create new store
- `GET /api/v1/stores/{store_id}` - Get store details
- `DELETE /api/v1/stores/{store_id}` - Delete store

### Proxy Configuration

Vite is configured to proxy API requests to the backend:

```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true
  }
}
```

This means requests to `/api/v1/*` from the dashboard are automatically forwarded to `http://localhost:5000/api/v1/*`.

