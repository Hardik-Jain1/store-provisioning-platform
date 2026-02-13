# Store Provisioning Platform

A Kubernetes-native control plane for provisioning isolated e-commerce stores (WooCommerce/Medusa) with namespace-per-store isolation, Helm-based deployment, and a Vue.js management dashboard.

**Live Demo:** [Coming Soon]  

---

## Table of Contents

- [Overview](#overview)
  - [What Problem Does It Solve?](#what-problem-does-it-solve)
  - [High-Level Architecture](#high-level-architecture)
- [Core Features](#core-features)
  - [Functional](#functional)
  - [Reliability & Operations](#reliability--operations)
  - [Local-to-Production](#local-to-production)
- [End-to-End Flow](#end-to-end-flow)
- [Prerequisites](#prerequisites)
  - [System Requirements](#system-requirements)
  - [Verify Installation](#verify-installation)
- [Local Setup (Minikube)](#local-setup-minikube)
  - [Step 1: Start Kubernetes Cluster](#step-1-start-kubernetes-cluster)
  - [Step 2: Install NGINX Ingress Controller](#step-2-install-nginx-ingress-controller)
  - [Step 3: Configure Local DNS](#step-3-configure-local-dns)
  - [Step 4: Setup Backend](#step-4-setup-backend)
  - [Step 5: Setup Dashboard](#step-5-setup-dashboard)
  - [Step 6: Verify Setup](#step-6-verify-setup)
- [How to Create a Store and Place an Order](#how-to-create-a-store-and-place-an-order)
  - [1. Open Dashboard](#1-open-dashboard)
  - [2. Create a New Store](#2-create-a-new-store)
  - [3. Wait for Provisioning](#3-wait-for-provisioning)
  - [4. Open Store Frontend](#4-open-store-frontend)
  - [5. Place a Test Order](#5-place-a-test-order)
  - [6. Verify Order in Admin Panel](#6-verify-order-in-admin-panel)
  - [7. Delete Store (Optional)](#7-delete-store-optional)
- [VPS / Production Setup (k3s)](#vps--production-setup-k3s)
  - [Step 1: Install k3s](#step-1-install-k3s-if-not-already-installed)
  - [Step 2: Configure DNS](#step-2-configure-dns)
  - [Step 3: Deploy Backend on VPS](#step-3-deploy-backend-on-vps)
  - [Step 4: Deploy Dashboard](#step-4-deploy-dashboard-optional---production-build)
  - [Step 5: What Changes Between Local and Production?](#step-5-what-changes-between-local-and-production)
  - [Step 6: Optional - TLS with cert-manager](#step-6-optional---tls-with-cert-manager)
  - [Step 7: Upgrade and Rollback](#step-7-upgrade-and-rollback)
- [System Design & Tradeoffs](#system-design--tradeoffs)
  - [Architecture Decisions](#architecture-decisions)
  - [Scaling Considerations](#scaling-considerations)
  - [Security Hardening](#security-hardening-implemented)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)

---

## Overview

This platform allows users to provision fully-functional e-commerce stores on Kubernetes with a single click. Each store runs in complete isolation with its own namespace, database, persistent storage, and ingress. The same Helm charts deploy to local clusters (Minikube/Kind) and production VPS (k3s) with only configuration changes.

### What Problem Does It Solve?

Traditional e-commerce hosting requires manual server setup, database configuration, and maintenance. This platform automates the entire lifecycle:
- **Provision:** Create a new store in ~2-3 minutes
- **Isolation:** Each store runs independently (namespace-per-store)
- **Scalability:** Provision multiple stores concurrently
- **Reliability:** Crash recovery, idempotency, clean teardown
- **Portability:** Same charts for local dev and production VPS

### High-Level Architecture

```
┌──────────────────┐
│  Vue.js Dashboard│  (Port 3000)
│  User Interface  │  - Create/view/delete stores
└────────┬─────────┘  - Real-time status updates
         │ REST API
         ↓
┌──────────────────────────────────────┐
│  Flask Backend (Control Plane)       │  (Port 5000)
│  ┌────────────────────────────────┐  │
│  │ Store Service (Business Logic) │  │
│  └───┬───────────────────────┬────┘  │
│      │                       │        │
│  ┌───▼──────┐      ┌─────────▼─────┐ │
│  │ Database │      │ Provisioning  │ │
│  │ (SQLite) │      │ Worker (Async)│ │
│  └──────────┘      └────────┬──────┘ │
│                              │        │
│         ┌────────────────────▼──────┐ │
│         │ Helm Service + K8s Client │ │
│         └───────────┬────────────────┘ │
└─────────────────────┼──────────────────┘
                      │
          ┌───────────▼───────────┐
          │  Helm + Kubernetes    │
          └───────────┬───────────┘
                      │
    ┌─────────────────┴─────────────────┐
    │                                    │
┌───▼───────────────┐        ┌──────────▼────────┐
│ Namespace:        │        │ Namespace:         │
│ store-abc123      │        │ store-xyz456       │
│                   │        │                    │
│ ├─ MySQL          │        │ ├─ MySQL           │
│ ├─ WordPress      │        │ ├─ WordPress       │
│ ├─ WooCommerce    │        │ ├─ WooCommerce     │
│ ├─ Setup Job      │        │ ├─ Setup Job       │
│ ├─ Services       │        │ ├─ Services        │
│ ├─ Ingress        │        │ ├─ Ingress         │
│ ├─ PVCs           │        │ ├─ PVCs            │
│ └─ Secrets        │        │ └─ Secrets         │
└───────────────────┘        └────────────────────┘
```

---

## Core Features

### Functional
- **Multi-store provisioning** - Concurrent, isolated store creation
- **Namespace-per-store isolation** - Complete resource separation
- **Helm-based deployment** - Production-ready templating engine
- **WooCommerce engine** - Fully functional with order placement
- **Persistent storage** - Database and uploads survive pod restarts
- **Ingress-based routing** - HTTP exposure with stable URLs
- **Automated setup** - Kubernetes Job installs WooCommerce, creates products
- **Clean teardown** - Delete stores safely with no orphaned resources

### Reliability & Operations
- **Idempotency** - Safe to retry store creation
- **Crash recovery** - Resume provisioning after backend restart
- **Failure handling** - Clear status and error reporting
- **Health checks** - Readiness/liveness probes on all components
- **Resource limits** - CPU/memory requests and limits
- **Secrets management** - Auto-generated credentials, no hardcoded secrets
- **Audit trail** - Timestamps and status history in database

### Local-to-Production
- **Environment flexibility** - Same Helm charts for local and VPS
- **Values-based configuration** - `values-local.yaml` vs `values-prod.yaml`
- **Upgrade/rollback support** - Helm release management

---

## End-to-End Flow

1. **User creates store** via dashboard → `POST /stores` with name, engine, credentials
2. **Backend creates record** in database with status `PROVISIONING`
3. **Backend invokes Helm** → `helm install store-{id} ./helm/store --set ...`
4. **Helm renders and applies** templates → Namespace, MySQL, WordPress, Job, Ingress, Secrets
5. **Kubernetes provisions** resources → Pulls images, attaches PVCs, runs setup Job
6. **Setup Job completes** → Installs WordPress, activates WooCommerce, creates products
7. **Backend polls Kubernetes** → Checks pod readiness and Job status
8. **Backend updates status** → `READY` with store URL
9. **User visits store** → Places order, confirms in admin panel
10. **User deletes store** → `helm uninstall` + namespace deletion

**Database is the source of truth. Kubernetes is the execution engine.**

---

## Prerequisites

### System Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| **Docker** | 20+ | Container runtime |
| **kubectl** | 1.23+ | Kubernetes CLI |
| **Helm** | 3.10+ | Package manager |
| **Minikube** / **Kind** | Latest | Local Kubernetes cluster |
| **Python** | 3.9+ | Backend runtime |
| **Node.js** | 18+ | Dashboard build |

### Verify Installation

```bash
# Check Docker
docker --version

# Check kubectl
kubectl version --client

# Check Helm
helm version

# Check Python
python --version

# Check Node.js
node --version
npm --version
```

---

## Local Setup (Minikube)

### Step 1: Start Kubernetes Cluster

```bash
# Start Minikube with sufficient resources
minikube start --driver=docker

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

### Step 2: Install NGINX Ingress Controller

```bash
# Enable ingress addon
minikube addons enable ingress

# Verify ingress controller is running
kubectl get pods -n ingress-nginx
```

### Step 3: Configure Local DNS

**Option A: Edit hosts file** 

```bash
# Get Minikube IP
minikube ip

# Add entries to /etc/hosts (Linux/Mac) or C:\Windows\System32\drivers\etc\hosts (Windows)
# Replace <MINIKUBE_IP> with the actual IP from above
<MINIKUBE_IP>  mystore.localhost
<MINIKUBE_IP>  testshop.localhost
<MINIKUBE_IP>  demo.localhost
```

**Option B: Use minikube tunnel** (Recommended)

```bash
# Run in a separate terminal (requires sudo/admin)
minikube tunnel
```

### Step 4: Setup Backend

**Option A: Using uv (Recommended - Fast)**

```bash
cd backend

# This creates venv and installs dependencies in one step
uv sync

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

```

**Option B: Using standard Python venv**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
**Create .env**
```bash
# Database
DATABASE_URL=sqlite:///store_platform.db

# Helm
HELM_CHART_PATH=helm/store
HELM_VALUES_FILE=values.yaml
HELM_ENV_VALUES_FILE=values-local.yaml

# Kubernetes
# KUBECONFIG=/path/to/kubeconfig  # Optional, uses default if not set

# Provisioning
PROVISIONING_TIMEOUT_SECONDS=600  # 10 minutes
PROVISIONING_POLL_INTERVAL_SECONDS=5
PROVISIONING_MAX_WORKERS=5

# Domain
BASE_DOMAIN=localhost

# Logging
LOG_DIR=logs  # Directory for log files
LOG_FILE=store_platform.log  # Log file name

# Flask
FLASK_HOST=0.0.0.0
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
```

**Start backend server**
```bash
python app.py
```

Backend will start on `http://localhost:5000`

### Step 5: Setup Dashboard

Open a new terminal:

```bash
cd dashboard

# Install dependencies
npm install

# Create .env file
echo "VITE_API_BASE_URL=/api/v1" > .env

# Start development server
npm run dev
```

Dashboard will start on `http://localhost:3000`

### Step 6: Verify Setup

```bash
# Check backend health
curl http://localhost:5000/health

# Expected output:
# {"status": "healthy"}

# Check stores API
curl http://localhost:5000/stores

# Expected output (empty list initially):
# {"stores": []}
```

---

## How to Create a Store and Place an Order

### 1. Open Dashboard

Navigate to `http://localhost:3000` in your browser.

### 2. Create a New Store

1. Click **"+ Create New Store"** button
2. Fill in the form:
   - **Store Name:** `mystore` (lowercase, alphanumeric, hyphens)
   - **Engine:** Select `WooCommerce`
   - **Admin Username:** `storeadmin`
   - **Admin Email:** `admin@mystore.com`
   - **Admin Password:** `SecurePass123!`
3. Click **"Create Store"**

### 3. Wait for Provisioning

- Store card appears with status badge: **🔵 PROVISIONING**
- Dashboard auto-refreshes every 5 seconds
- Provisioning takes ~2-3 minutes (first time may be longer due to image pulls)
- Status updates automatically to **🟢 READY** when complete

**Behind the scenes:**
```bash
# You can watch provisioning progress in a terminal:
kubectl get pods -n store-<id> --watch

# Check Helm release:
helm list -n store-<id>

# View setup job logs:
kubectl logs -n store-<id> job/<id>-setup-job -f
```

### 4. Open Store Frontend

Once status is **READY**:
1. Click **"Open Store"** button on the store card
2. Store opens in new tab at `http://mystore.localhost`
3. You should see WooCommerce storefront with sample products

### 5. Place a Test Order

1. Browse products on the storefront
2. Click **"Add to cart"** on any product
3. Click **"View cart"** or cart icon
4. Proceed to **"Checkout"**
5. Fill in billing details:
   ```
   First name: Test
   Last name: User
   Email: test@example.com
   Phone: 1234567890
   Address: 123 Test St
   City: Test City
   Postcode: 12345
   ```
6. Select **"Cash on Delivery"** as payment method
7. Click **"Place order"**
8. You should see **"Order received"** confirmation page

### 6. Verify Order in Admin Panel

1. Navigate to `http://mystore.localhost/wp-admin`
2. Login with credentials from step 2:
   - **Username:** `storeadmin`
   - **Password:** `SecurePass123!`
3. In WordPress admin, go to **WooCommerce → Orders**
4. Your test order should be listed with status **"Processing"**

**Success! You've provisioned a store and placed an order end-to-end.**

### 7. Delete Store (Optional)

1. Return to dashboard
2. Click **"Delete Store"** on the store card
3. Confirm deletion in the dialog
4. Status changes to **DELETING** → **DELETED**
5. All resources are cleaned up:
   ```bash
   # Verify deletion
   kubectl get namespace store-<id>  # Should return "not found"
   helm list --all-namespaces | grep store-<id>  # Should be empty
   ```

---

## VPS / Production Setup (k3s)

### Assumptions

- VPS with Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- Public IP address
- Domain name pointed to VPS (e.g., `example.com` → VPS IP)
- k3s installed on the VPS

### Step 1: Install k3s (if not already installed)

```bash
# On your VPS
curl -sfL https://get.k3s.io | sh -

# Verify installation
sudo k3s kubectl get nodes

# Get kubeconfig for remote access (optional)
sudo cat /etc/rancher/k3s/k3s.yaml
```

### Step 2: Configure DNS

Point wildcard DNS to your VPS IP:

```
*.stores.example.com  →  <VPS_IP>
```

Or create individual A records:

```
mystore.example.com   →  <VPS_IP>
testshop.example.com  →  <VPS_IP>
```

### Step 3: Deploy Backend on VPS

```bash
# SSH into VPS
ssh user@your-vps-ip

# Clone repository
git clone <your-repo-url>
cd store-provisioning-platform/backend

# Install Python dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env for production
cat > .env << EOF
DATABASE_URL=sqlite:///store_platform.db
HELM_CHART_PATH=helm/store
HELM_VALUES_FILE=values.yaml
HELM_ENV_VALUES_FILE=values-local.yaml
# KUBECONFIG=/path/to/kubeconfig  # Optional, uses default if not set
PROVISIONING_TIMEOUT_SECONDS=600  # 10 minutes
PROVISIONING_POLL_INTERVAL_SECONDS=5
PROVISIONING_MAX_WORKERS=5
BASE_DOMAIN=localhost
LOG_DIR=logs  # Directory for log files
LOG_FILE=store_platform.log  # Log file name
FLASK_HOST=0.0.0.0
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
EOF

# Run backend as a service (using systemd)
sudo tee /etc/systemd/system/store-backend.service > /dev/null << EOF
[Unit]
Description=Store Provisioning Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment="PATH=$PWD/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=$PWD/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start backend service
sudo systemctl daemon-reload
sudo systemctl enable store-backend
sudo systemctl start store-backend
sudo systemctl status store-backend
```

### Step 4: Deploy Dashboard (Optional - Production Build)

```bash
cd dashboard

# Install Node.js on VPS if not present
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Build dashboard
npm install
npm run build

# Serve static files with nginx
sudo apt install nginx -y

sudo tee /etc/nginx/sites-available/store-dashboard > /dev/null << EOF
server {
    listen 80;
    server_name dashboard.example.com;
    root $PWD/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/store-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5: What Changes Between Local and Production?

The same Helm charts work for both environments. Changes are handled via `values-prod.yaml`:

| Aspect | Local (`values-local.yaml`) | Production (`values-prod.yaml`) |
|--------|----------------------------|--------------------------------|
| **Domain** | `*.localhost` | `*.stores.example.com` |
| **Ingress Class** | `nginx` | `nginx` (or `traefik` for k3s) |
| **TLS** | Disabled | Enabled with cert-manager |
| **Storage Class** | `standard` (Minikube default) | `local-path` (k3s default) |
| **Storage Size** | 2Gi (WordPress), 5Gi (MySQL) | 10Gi (WordPress), 20Gi (MySQL) |
| **Secrets** | Auto-generated per store | Auto-generated per store |
| **Resource Limits** | Minimal (dev workload) | Production-appropriate |

**Example: Production values override**

```yaml
# values-prod.yaml
ingress:
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  tls:
    enabled: true

woocommerce:
  wordpress:
    persistence:
      storageClass: "local-path"
      size: "10Gi"
  mysql:
    persistence:
      storageClass: "local-path"
      size: "20Gi"
```

### Step 6: Optional - TLS with cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

# Wait for cert-manager pods
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=120s

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

Now when you create stores with `values-prod.yaml`, TLS certificates are automatically provisioned.

### Step 7: Upgrade and Rollback

```bash
# Upgrade a store (e.g., change WordPress version)
helm upgrade store-abc123 ./helm/store \
  --namespace store-abc123 \
  -f values.yaml \
  -f values-prod.yaml \
  --set woocommerce.wordpress.image.tag=6.4-php8.2-apache

# Rollback if something goes wrong
helm rollback store-abc123 --namespace store-abc123

# View release history
helm history store-abc123 --namespace store-abc123
```

---

## System Design & Tradeoffs

### Architecture Decisions

#### 1. **Control Plane Pattern (Backend as Orchestrator)**

**Decision:** Backend doesn't generate YAML or manage pods directly. It invokes Helm and monitors Kubernetes.

**Rationale:**
- Separation of concerns: Backend handles business logic, Helm handles deployment
- Helm templates are maintainable and version-controlled
- Helm provides built-in upgrade/rollback capabilities
- No need to reimplement Kubernetes resource templating

**Tradeoff:** Adds Helm CLI dependency. Alternative would be using Helm SDK (Go library) or Kubernetes client directly, but this adds complexity without significant benefit for this use case.

---

#### 2. **Namespace-Per-Store Isolation**

**Decision:** Each store runs in a dedicated namespace (e.g., `store-abc123`).

**Rationale:**
- **Blast radius control:** Issues in one store don't affect others
- **Clean teardown:** `kubectl delete namespace` removes all resources
- **Resource quotas:** Can enforce limits per store (not implemented yet, but architecture supports it)
- **Security:** NetworkPolicies can isolate store traffic (future enhancement)

**Tradeoff:** More namespaces mean more Kubernetes objects to manage. For very high store counts (thousands), may need cluster-level optimizations.

---

#### 3. **Database as Source of Truth**

**Decision:** SQLite database records are created **before** Helm install. Kubernetes state is derived from DB.

**Rationale:**
- **Idempotency:** Retry-safe. If Helm fails midway, DB shows what was intended
- **Crash recovery:** Backend can resume provisioning on restart by querying DB
- **Audit trail:** Complete history of store lifecycle (creation, updates, deletion)
- **Dashboard state:** Dashboard polls backend API, not Kubernetes directly

**Tradeoff:** Two sources of truth to keep in sync (DB and Kubernetes). Reconciliation loop in provisioning worker ensures eventual consistency.

---

#### 4. **Asynchronous Provisioning (ThreadPoolExecutor)**

**Decision:** Provisioning happens in background threads, not in API request path.

**Rationale:**
- **Responsiveness:** API returns immediately with status `PROVISIONING`
- **Concurrency:** Multiple stores can provision simultaneously (up to `max_workers=5`)
- **Timeout handling:** Long-running provisioning doesn't block API server
- **User experience:** Dashboard shows real-time status updates

**Tradeoff:** Adds complexity (threading, shared state, cleanup). Alternative would be synchronous provisioning or external job queue (Celery), but ThreadPoolExecutor is sufficient for moderate scale.

---

#### 5. **Idempotency Strategy**

**Implementation:**
- Store records have unique names (enforced by DB constraint)
- API checks for existing store before creating
- If store exists with status `PROVISIONING`, backend resumes monitoring
- Helm installs are idempotent (install fails if release already exists, upgrade can be used)

**How it handles failures:**
- User retries store creation → Backend returns 409 Conflict if name exists
- Backend crashes mid-provisioning → On restart, `resume_provisioning_stores()` continues monitoring
- Helm install fails → Store marked `FAILED` with reason, user can delete and retry with different name

---

#### 6. **Failure Handling**

**Decision:** Fail explicitly, don't auto-delete failed stores.

**Rationale:**
- **Debugging:** User can inspect failed resources (`kubectl describe`, `kubectl logs`)
- **Transparency:** Clear error messages in dashboard
- **No data loss:** User decides when to delete

**Example failure scenarios:**
- MySQL pod CrashLoopBackOff → Status: `FAILED`, Reason: "MySQL pod not ready"
- Setup Job fails → Status: `FAILED`, Reason: "Setup job did not complete"
- Timeout (10 minutes) → Status: `FAILED`, Reason: "Provisioning timed out"

---

#### 7. **Cleanup Guarantees**

**Decision:** Store deletion uses `helm uninstall` + `kubectl delete namespace`.

**Rationale:**
- **No orphaned resources:** Namespace deletion removes all objects (PVCs, Secrets, Services, Pods)
- **Helm-managed cleanup:** Helm tracks what it created, uninstall removes those resources
- **Double-check with namespace deletion:** Even if Helm leaves something, namespace deletion catches it

**Tradeoff:** PVC deletion means data is lost (by design). For backup/archival, would need to add backup step before deletion.

---

#### 8. **What Changes for Production?**

| Component | Local | Production | How It's Handled |
|-----------|-------|-----------|------------------|
| **Domains** | `*.localhost` | `*.yourdomain.com` | `BASE_DOMAIN` env var + Helm values |
| **Ingress** | Minikube nginx | VPS nginx/traefik | `ingress.className` in values |
| **TLS** | None | cert-manager | `ingress.tls.enabled=true` in values-prod |
| **Storage** | `standard` (hostPath) | `local-path` or cloud | `storageClass` in values |
| **Secrets** | Auto-generated per store | Auto-generated per store | Same mechanism |
| **Resource Limits** | Minimal (dev) | Production-tuned | `resources` in values |
| **Persistence Size** | 2Gi/5Gi | 10Gi/20Gi | `persistence.size` in values |

**Key Insight:** Architecture is identical. Only configuration differs. This is the power of Helm + environment-specific values files.

---

### Scaling Considerations

#### Horizontal Scaling (What Scales)

| Component | Scalable? | How? |
|-----------|-----------|------|
| **Dashboard** | Yes | Stateless, can run multiple instances behind load balancer |
| **Backend API** | Yes | Stateless (except SQLite), can use Postgres + read replicas |
| **Provisioning Worker** | Limited | ThreadPoolExecutor is single-process. Could use multi-process or distributed queue (Celery + Redis) |
| **Store Workloads** | Yes | WordPress can scale horizontally with shared PVC/EFS and session handling |
| **MySQL** | Stateful | Vertical scaling or managed MySQL (RDS/Cloud SQL) for high load |

#### Provisioning Throughput

Current design provisions ~5 stores concurrently (ThreadPoolExecutor with `max_workers=5`).

**To increase throughput:**
1. Increase `max_workers` (limited by backend CPU/memory)
2. Use distributed task queue (Celery + Redis/RabbitMQ)
3. Multiple backend instances coordinating via DB locks

**Bottleneck:** Kubernetes API rate limits, cluster resource capacity, image pull times (first time).

#### Stateful Constraints

- **SQLite:** Single-writer, not suitable for multi-backend deployment. Migrate to PostgreSQL for production at scale.
- **MySQL per store:** Each store has its own MySQL, doesn't share. Could use shared managed MySQL cluster if cost is concern.

---

### Security Hardening (Implemented)

- Auto-generated secrets (no hardcoded passwords)
- Secrets stored in Kubernetes Secrets (not in Git)
- Namespace isolation (each store is a separate namespace)
- Resource limits (prevents resource exhaustion)

---

## Project Structure

```
store-provisioning-platform/
├── backend/                    # Flask control plane
│   ├── app.py                  # Main application entry point
│   ├── config.py               # Environment configuration
│   ├── requirements.txt        # Python dependencies
│   │
│   ├── api/                    # REST API layer
│   │   └── stores.py           # Store CRUD endpoints
│   │
│   ├── models/                 # Database models
│   │   └── store.py            # Store model (SQLAlchemy)
│   │
│   ├── services/               # Business logic
│   │   ├── store_service.py    # Store lifecycle management
│   │   ├── helm_service.py     # Helm CLI wrapper
│   │   └── k8s_service.py      # Kubernetes client wrapper
│   │
│   ├── workers/                # Async provisioning
│   │   └── provisioning.py     # ThreadPoolExecutor worker
│   │
│   ├── db/                     # Database setup
│   │   └── session.py          # SQLAlchemy session management
│   │
│   └── helm/                   # Helm charts
│       └── store/              # Store provisioning chart
│           ├── Chart.yaml
│           ├── values.yaml
│           ├── values-local.yaml
│           ├── values-prod.yaml
│           └── templates/      # Kubernetes manifests
│
├── dashboard/                  # Vue.js frontend
│   ├── src/
│   │   ├── App.vue             # Main app component
│   │   ├── components/         # UI components
│   │   └── api/                # API client
│   ├── package.json
│   └── vite.config.js
│
└── README.md                   # This file
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Vue 3 + Vite | Modern reactive UI |
| **Backend** | Flask + Flask-RESTful | Lightweight REST API |
| **Database** | SQLite (SQLAlchemy) | Store metadata persistence |
| **Async Worker** | ThreadPoolExecutor | Concurrent provisioning |
| **Orchestration** | Helm 3 | Kubernetes package management |
| **Container Orchestration** | Kubernetes (Minikube/k3s) | Runtime environment |
| **Ingress** | NGINX Ingress Controller | HTTP routing |
| **Store Engine** | WooCommerce (WordPress + PHP + MySQL) | E-commerce functionality |

