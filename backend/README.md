# Store Provisioning Platform - Backend

## Overview

This is the **backend control plane** for the Store Provisioning Platform. It orchestrates the lifecycle of ecommerce stores (WooCommerce/Medusa) that are provisioned as isolated Kubernetes workloads via Helm.

**What the backend does:**
- Exposes REST APIs for store management
- Persists store metadata and state in SQLite
- Invokes Helm CLI to install/uninstall store releases
- Monitors Kubernetes to determine provisioning success/failure
- Handles crash recovery and idempotency

**What the backend does NOT do:**
- Generate Kubernetes YAML manifests (that's Helm's job)
- Manage pods/services directly (that's Kubernetes' job)
- Implement ecommerce logic (that's WooCommerce/Medusa's job)

---

## Architecture

```
┌─────────────┐
│  Dashboard  │ (React - not implemented here)
└──────┬──────┘
       │ REST API
       ↓
┌─────────────────────────────────────┐
│  Backend Control Plane (Flask)      │
│  ┌──────────────────────────────┐   │
│  │  API Layer (stores.py)       │   │
│  └────────────┬─────────────────┘   │
│               ↓                      │
│  ┌──────────────────────────────┐   │
│  │  Store Service               │   │
│  │  (business logic)            │   │
│  └──┬───────────────────────┬───┘   │
│     ↓                       ↓        │
│  ┌──────────┐       ┌──────────┐    │
│  │ Database │       │  Worker  │    │
│  │ (SQLite) │       │ (Async)  │    │
│  └──────────┘       └────┬─────┘    │
│                          ↓           │
│              ┌────────────────────┐  │
│              │  Helm Service      │  │
│              │  K8s Service       │  │
│              └──┬──────────────┬──┘  │
└─────────────────┼──────────────┼─────┘
                  ↓              ↓
            ┌──────────┐   ┌──────────┐
            │   Helm   │   │   K8s    │
            └──────────┘   └──────────┘
                  ↓              ↓
            ┌─────────────────────────┐
            │  Store Workloads        │
            │  (WooCommerce/Medusa)   │
            └─────────────────────────┘
```

---

## Prerequisites

### System Requirements

1. **Python 3.9+**
2. **Helm CLI** - Install from https://helm.sh/docs/intro/install/
3. **Kubernetes cluster** - Kind, Minikube, or k3s
4. **kubectl** - Configured to access your cluster

### Verify Prerequisites

```bash
# Check Python
python --version  # Should be 3.9+

# Check Helm
helm version

# Check kubectl and cluster access
kubectl cluster-info
kubectl get nodes
```

---

## Installation

### 1. Clone the repository

```bash
cd store-provisioning-platform/backend
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Verify Helm chart exists

The backend expects the Helm chart to be at:
```
../helm/store/
```

Verify it exists:
```bash
ls ../helm/store/Chart.yaml
```

---

## Configuration

The backend uses environment variables for configuration. Default values work for local development.

### Configuration Variables

Create a `.env` file (optional) or set environment variables:

```bash
# Database
DATABASE_URL=sqlite:///store_platform.db

# Helm
HELM_CHART_PATH=../helm/store
HELM_VALUES_FILE=values.yaml
HELM_ENV_VALUES_FILE=values-local.yaml

# Kubernetes
# KUBECONFIG=/path/to/kubeconfig  # Optional, uses default if not set

# Provisioning
PROVISIONING_TIMEOUT_SECONDS=600  # 10 minutes
PROVISIONING_POLL_INTERVAL_SECONDS=5

# Domain
BASE_DOMAIN=localhost

# Flask
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
```

---

## Running the Backend

### Start the Flask application

```bash
python app.py
```

You should see output like:

```
============================================================
Store Provisioning Platform - Backend Control Plane
============================================================
Initializing database...
Database initialized successfully
Initializing services...
✓ HelmService initialized
✓ K8sService initialized
✓ StoreService initialized
Initializing provisioning worker...
✓ ProvisioningWorker started
Checking for stores to resume...
Found 0 stores in PROVISIONING state
Initializing API routes...
✓ API routes registered
============================================================
Backend initialization complete
============================================================
Starting Flask development server on port 5000...
API available at: http://localhost:5000
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

### Health Check

```bash
curl http://localhost:5000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "service": "store-provisioning-backend"
}
```

### Create Store

```bash
curl -X POST http://localhost:5000/api/v1/stores \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-store",
    "engine": "woocommerce"
  }'
```

Response (202 Accepted):
```json
{
  "id": "my-store-abc123",
  "name": "my-store",
  "engine": "woocommerce",
  "namespace": "store-my-store-abc123",
  "status": "PROVISIONING",
  "created_at": "2026-02-10T10:00:00"
}
```

**Note:** The API returns immediately. Provisioning happens asynchronously in the background.

### List Stores

```bash
curl http://localhost:5000/api/v1/stores
```

Response:
```json
{
  "stores": [
    {
      "id": "my-store-abc123",
      "name": "my-store",
      "engine": "woocommerce",
      "namespace": "store-my-store-abc123",
      "status": "READY",
      "store_url": "http://my-store.localhost",
      "failure_reason": null,
      "created_at": "2026-02-10T10:00:00",
      "updated_at": "2026-02-10T10:05:00"
    }
  ]
}
```

### Get Store

```bash
curl http://localhost:5000/api/v1/stores/my-store-abc123
```

Response:
```json
{
  "id": "my-store-abc123",
  "name": "my-store",
  "engine": "woocommerce",
  "namespace": "store-my-store-abc123",
  "helm_release": "my-store-abc123",
  "status": "READY",
  "store_url": "http://my-store.localhost",
  "failure_reason": null,
  "created_at": "2026-02-10T10:00:00",
  "updated_at": "2026-02-10T10:05:00"
}
```

### Delete Store

```bash
curl -X DELETE http://localhost:5000/api/v1/stores/my-store-abc123
```

Response:
```json
{
  "id": "my-store-abc123",
  "status": "DELETED",
  "message": "Store deleted successfully"
}
```

---

## Testing the Backend

### 1. Test health endpoint

```bash
curl http://localhost:5000/health
```

### 2. Create a store

```bash
curl -X POST http://localhost:5000/stores \
  -H "Content-Type: application/json" \
  -d '{"name": "test-store", "engine": "woocommerce"}'
```

### 3. Check store status

```bash
curl http://localhost:5000/stores
```

Watch the backend logs to see provisioning progress.

### 4. Verify in Kubernetes

```bash
# List namespaces
kubectl get namespaces | grep store-

# Check pods in store namespace
kubectl get pods -n store-test-store-abc123

# Check helm releases
helm list -A
```

### 5. Delete store

```bash
curl -X DELETE http://localhost:5000/stores/test-store-abc123
```

---

## Store Lifecycle States

The backend tracks stores through these states:

1. **PROVISIONING** - Store is being created
   - Database record created
   - Helm install in progress
   - Kubernetes resources being created

2. **READY** - Store is fully operational
   - All pods are running
   - Setup job completed
   - Ingress is available
   - Store URL is accessible

3. **FAILED** - Provisioning failed
   - Failure reason is logged
   - Resources may be partially created
   - User must decide whether to delete or debug

4. **DELETING** - Store is being deleted
   - Helm uninstall in progress

5. **DELETED** - Store has been removed
   - All Kubernetes resources cleaned up
   - Record remains in database for audit

---

## How Provisioning Works

### Step-by-step flow:

1. **API receives POST /stores request**
   - Validates input (name, engine)
   - Creates store record in database with status=PROVISIONING
   - Returns immediately to client

2. **Provisioning worker picks up task**
   - Runs in background thread
   - Fetches store from database

3. **Helm install**
   - Worker invokes Helm CLI
   - Helm renders templates and applies to Kubernetes
   - Namespace, pods, services, ingress created

4. **Readiness polling**
   - Worker polls Kubernetes every 5 seconds
   - Checks: pods ready, setup job succeeded, ingress available
   - Timeout after 10 minutes

5. **Update status**
   - If ready: status=READY, store_url set
   - If failed: status=FAILED, failure_reason set

---

## Idempotency and Crash Recovery

### Idempotency guarantees:

- Store names are unique (enforced by database)
- Helm release names are deterministic (= store ID)
- Namespaces are deterministic (store-{id})
- Retrying a failed provisioning is safe

### Crash recovery:

When the backend restarts:

1. Scans database for stores in PROVISIONING state
2. Checks if Helm release exists for each
3. If yes: Resumes readiness checks
4. If no: Restarts Helm install

This ensures no orphaned resources and graceful recovery.

---

## Troubleshooting

### Backend won't start

**Error: "Helm CLI not found"**
- Install Helm: https://helm.sh/docs/intro/install/

**Error: "Failed to load Kubernetes config"**
- Verify kubectl is configured: `kubectl cluster-info`
- Check KUBECONFIG environment variable

**Error: "Helm chart not found"**
- Verify chart exists at `../helm/store/Chart.yaml`
- Update `HELM_CHART_PATH` if needed

### Store stuck in PROVISIONING

Check backend logs for details:
```bash
# Look for errors in backend output
```

Check Kubernetes resources:
```bash
kubectl get pods -n store-{store-id}
kubectl describe pod -n store-{store-id}
kubectl logs -n store-{store-id} {pod-name}
```

Check Helm release:
```bash
helm list -n store-{store-id}
helm status {release-name} -n store-{store-id}
```

### Store failed to provision

Check `failure_reason` in API response:
```bash
curl http://localhost:5000/stores/{store-id}
```

Common failures:
- **"Helm install failed"** - Check Helm chart validity
- **"Setup job failed"** - Check job logs in Kubernetes
- **"Pods not ready"** - Check pod status and logs
- **"Provisioning timed out"** - Increase timeout or check resource constraints

---

## Project Structure

```
backend/
├── api/
│   ├── __init__.py
│   └── stores.py              # REST API routes
├── db/
│   ├── __init__.py
│   └── session.py             # Database session management
├── models/
│   ├── __init__.py
│   └── store.py               # Store model (SQLAlchemy)
├── services/
│   ├── __init__.py
│   ├── helm_service.py        # Helm CLI interactions
│   ├── k8s_service.py         # Kubernetes API (read-only)
│   └── store_service.py       # Business logic
├── workers/
│   ├── __init__.py
│   └── provisioning.py        # Async provisioning worker
├── app.py                     # Main Flask application
├── config.py                  # Configuration
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── store_platform.db          # SQLite database (created at runtime)
```

---

## Design Principles

This backend follows strict design principles from the implementation plan:

1. **Database is the source of truth**
   - All state stored in DB before Kubernetes operations
   - Enables idempotency and crash recovery

2. **Backend is a control plane, not a data plane**
   - Delegates to Helm for provisioning
   - Delegates to Kubernetes for runtime
   - Never generates YAML or manages resources directly

3. **Async provisioning**
   - API returns immediately
   - Worker handles long-running operations
   - No blocking requests

4. **Deterministic identifiers**
   - Helm release name = store ID
   - Namespace = store-{id}
   - Enables safe retries

5. **Explicit failure handling**
   - All failures logged with reasons
   - Stores marked as FAILED, not deleted
   - User maintains control

---

## Next Steps

1. **Implement Dashboard** - React UI to consume these APIs
2. **Add Medusa Support** - Currently only WooCommerce is fully implemented
3. **Add Authentication** - Secure the API endpoints
4. **Add Metrics** - Prometheus metrics for observability
5. **Production Deployment** - Deploy backend to VPS alongside k3s

---

## License

This is a demonstration project. All code is yours to use.

---

## Support

For questions or issues, refer to:
- Backend implementation plan: `../docs/backend_implementation_plan.md`
- System design: `../docs/system_design.md`
- Helm chart documentation: `../helm/README.md`
