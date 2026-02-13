# Store Provisioning Platform - Dashboard

A modern, production-ready Vue 3 dashboard for managing ecommerce store provisioning on Kubernetes.

## 🚀 Features

- **Store Management**: Create, view, and delete stores
- **Real-time Status Updates**: Automatic polling for store status changes
- **Clean Modern UI**: Minimalist, professional design
- **Responsive**: Works seamlessly on desktop and mobile
- **Health Monitoring**: Real-time API health status indicator
- **Error Handling**: Comprehensive error handling and user feedback
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

## 🎨 UI/UX Features

### Status Color Coding

- **Blue (Provisioning)**: Pulsing dot animation indicates active provisioning
- **Green (Ready)**: Solid green indicates store is operational
- **Red (Failed)**: Indicates provisioning failure with reason displayed
- **Orange (Deleting)**: Pulsing dot animation during deletion
- **Gray (Deleted)**: Indicates store has been removed

### Responsive Design

- Desktop: Grid layout with multiple columns
- Tablet: Adjusted grid with fewer columns
- Mobile: Single column layout with stacked elements

### Loading States

- Spinner animation during initial load
- Disabled buttons during operations
- Loading text for user feedback

### Empty States

- Friendly message when no stores exist
- Quick action button to create first store

### Error Handling

- API errors displayed with clear messages
- Toast notifications for user actions
- Retry options for failed operations

## 🔧 Configuration

### Backend URL

If your backend runs on a different host/port, update the proxy configuration in `vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-url:port',
      changeOrigin: true
    }
  }
}
```

### Polling Interval

To change the status polling interval, edit `App.vue`:

```javascript
const startPolling = () => {
  pollingInterval = setInterval(() => {
    // ... polling logic
  }, 5000); // Change this value (in milliseconds)
};
```

## 🐛 Troubleshooting

### Dashboard won't start

- Ensure Node.js 18+ is installed: `node --version`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

### API calls failing

- Verify backend is running on `http://localhost:5000`
- Check backend health: `curl http://localhost:5000/api/v1/health`
- Check browser console for CORS errors

### Stores not updating

- Check if polling is working (open browser console)
- Manually click the Refresh button
- Verify backend is accessible

## 📝 Development Notes

### State Management

- Uses Vue 3 Composition API with reactive refs
- No external state management library needed for this scope
- API logic cleanly separated in `storeApi.js`

### Component Architecture

- **App.vue**: Main container, handles state and API calls
- **StoreList.vue**: Presentational component for store list
- **StoreCard.vue**: Individual store card with actions
- **CreateStoreModal.vue**: Form modal for store creation
- **StatusBadge.vue**: Reusable status indicator

### Best Practices

- ✅ Clean separation of concerns
- ✅ Reusable components
- ✅ Proper error handling
- ✅ Loading states for better UX
- ✅ Responsive design
- ✅ Accessibility considerations
- ✅ No hardcoded data or endpoints

## 🚢 Production Deployment

### Build Optimization

```bash
npm run build
```

This creates an optimized production build with:
- Minified JavaScript and CSS
- Tree-shaking for smaller bundle size
- Asset optimization

### Serving the Build

You can serve the production build using any static file server:

```bash
# Using Python
python -m http.server 8080 --directory dist

# Using Node.js serve package
npx serve dist

# Using nginx (place build in web root)
cp -r dist/* /var/www/html/
```

### Environment Variables

For production, you may want to use environment variables for the API URL:

1. Create `.env.production`:
```
VITE_API_BASE_URL=https://your-production-api.com
```

2. Update `storeApi.js`:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
```

---

**Built with ❤️ using Vue 3 + Vite**
