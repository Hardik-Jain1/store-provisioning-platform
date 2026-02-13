# Store Provisioning Helm Chart

A production-ready Helm chart for provisioning isolated e-commerce stores (WooCommerce/Medusa) on Kubernetes with namespace-per-store isolation.

## Overview

This Helm chart is the **core deployment mechanism** for the Store Provisioning Platform. Each store is deployed as a single Helm release with complete isolation in its own namespace.

### Key Features

- **Namespace-per-store isolation**: Each store runs in its own namespace with dedicated resources
- **Multi-engine support**: WooCommerce (fully implemented), Medusa (stub)
- **Production-ready**: Includes probes, resource limits, secrets management, and persistent storage
- **Environment flexibility**: Same chart works for local (kind/minikube) and production (k3s/VPS) via values files
- **Idempotent**: Safe to upgrade and uninstall with clean teardown
- **Automated setup**: Setup Job handles complete e-commerce configuration
- **End-to-end functional**: Stores support placing orders immediately after provisioning

## Architecture

### WooCommerce Stack

```
Namespace: store-{id}
├── MySQL (StatefulSet)
│   └── PVC: mysql-data (10Gi)
├── WordPress + WooCommerce (Deployment)
│   └── PVC: wordpress-uploads (5Gi)
├── Setup Job (Job)
│   ├── Installs WordPress
│   ├── Activates WooCommerce
│   ├── Creates sample products
│   ├── Enables COD payment
│   └── Configures permalinks
├── Services (ClusterIP)
│   ├── MySQL (internal)
│   └── WordPress (internal)
├── Ingress
│   └── Routes: {store.domain} → WordPress
└── Secrets
    ├── DB credentials (auto-generated)
    └── Admin credentials (auto-generated)
```

### How Backend Calls This Chart

The backend calls Helm via CLI with dynamic values:

```bash
helm install {store.id} ./helm/store \
  --namespace {store.namespace} \
  --create-namespace \
  -f values.yaml \
  -f values-local.yaml \
  --set store.id={id} \
  --set store.name={name} \
  --set store.namespace={namespace} \
  --set store.engine={engine} \
  --set store.domain={domain}
```

**Critical Design:**
- Release name = `store.id`
- Namespace = `store.namespace`
- All store identity comes from `--set` values (not hardcoded)
- Chart uses `{{ .Release.Namespace }}` consistently

## Directory Structure

```
helm/store/
├── Chart.yaml                  # Chart metadata
├── values.yaml                 # Default values (all configurable)
├── values-local.yaml           # Local environment overrides
├── values-prod.yaml            # Production environment overrides
├── templates/
│   ├── _helpers.tpl            # Template helpers and functions
│   ├── namespace.yaml          # Namespace with labels/annotations
│   ├── secrets.yaml            # Auto-generated secrets
│   ├── ingress.yaml            # Engine-agnostic ingress
│   ├── engine.yaml             # Engine selector logic
│   ├── engine/
│   │   ├── woocommerce/
│   │   │   ├── mysql.yaml          # MySQL StatefulSet + Service + PVC
│   │   │   ├── wordpress.yaml      # WordPress Deployment + Service + PVC
│   │   │   └── setup-job.yaml      # WooCommerce setup automation
│   │   └── medusa/
│   │       └── stub.yaml           # Medusa placeholder
│   └── NOTES.txt               # Post-install instructions
```

## Usage

### Prerequisites

- Kubernetes cluster (kind/minikube/k3s)
- Helm 3.x installed
- Ingress controller (nginx recommended)
- Storage provisioner with default StorageClass

### Local Installation Example

```bash
# Install a WooCommerce store locally
helm install store-abc123 ./helm/store \
  --namespace store-abc123 \
  --create-namespace \
  -f values.yaml \
  -f values-local.yaml \
  --set store.id=abc123 \
  --set store.name="My Test Store" \
  --set store.namespace=store-abc123 \
  --set store.engine=woocommerce \
  --set store.domain=abc.localhost
```

### Production Installation Example

```bash
# Install a WooCommerce store on VPS (k3s)
helm install store-xyz789 ./helm/store \
  --namespace store-xyz789 \
  --create-namespace \
  -f values.yaml \
  -f values-prod.yaml \
  --set store.id=xyz789 \
  --set store.name="Production Store" \
  --set store.namespace=store-xyz789 \
  --set store.engine=woocommerce \
  --set store.domain=store.example.com
```

### Monitoring Setup Progress

```bash
# Watch setup job logs
kubectl logs -n store-abc123 job/store-abc123-woocommerce-setup -f

# Check pod status
kubectl get pods -n store-abc123 -w

# Wait for setup completion
kubectl wait --for=condition=complete --timeout=600s \
  job/store-abc123-woocommerce-setup -n store-abc123
```

### Upgrading a Store

```bash
# Upgrade chart (e.g., change resource limits)
helm upgrade store-abc123 ./helm/store \
  --namespace store-abc123 \
  -f values.yaml \
  -f values-local.yaml \
  --set store.id=abc123 \
  --set store.name="My Test Store" \
  --set store.namespace=store-abc123 \
  --set store.engine=woocommerce \
  --set store.domain=abc.localhost
```

### Uninstalling a Store

```bash
# Remove all resources
helm uninstall store-abc123 -n store-abc123

# Delete namespace (includes PVCs)
kubectl delete namespace store-abc123
```

## Configuration

### Required Values (Must be set via --set)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `store.id` | Unique store identifier (release name) | `abc123` |
| `store.name` | Human-readable store name | `My Store` |
| `store.namespace` | Kubernetes namespace | `store-abc123` |
| `store.engine` | Engine type | `woocommerce` or `medusa` |
| `store.domain` | Ingress domain | `abc.localhost` or `store.example.com` |

### Important Configurable Values

#### Ingress Configuration

```yaml
ingress:
  enabled: true
  className: "nginx"
  tls:
    enabled: false  # Set true for production with cert-manager
```

#### Storage Configuration

```yaml
woocommerce:
  wordpress:
    persistence:
      storageClass: ""  # Empty = cluster default
      size: "5Gi"
  mysql:
    persistence:
      storageClass: ""
      size: "10Gi"
```

#### Resource Limits

```yaml
woocommerce:
  wordpress:
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
```

#### Secrets (Auto-generated if not provided)

```yaml
secrets:
  database:
    rootPassword: ""  # Auto-generated with randAlphaNum(32)
    username: "storeuser"
    password: ""      # Auto-generated
    name: "storedb"
  admin:
    username: "admin"
    password: ""      # Auto-generated with randAlphaNum(24)
    email: "admin@example.com"
```

## Environment-Specific Overrides

### Local (values-local.yaml)

- Lower resource requests/limits for laptop development
- `storageClass: "standard"` (kind/minikube default)
- TLS disabled
- Suitable for kind/minikube/k3d

### Production (values-prod.yaml)

- Higher resource requests/limits for stable performance
- `storageClass: "local-path"` (k3s default) or cloud provider class
- TLS enabled with cert-manager annotations
- Production-grade security settings

## WooCommerce Setup Job

The setup job (`setup-job.yaml`) automates complete WooCommerce configuration:

### What It Does

1. **Wait for WordPress** - Ensures WordPress HTTP endpoint is reachable
2. **Install WordPress Core** - Completes initial WordPress setup
3. **Install WooCommerce** - Installs and activates WooCommerce plugin
4. **Configure Store** - Sets store address, currency, basic settings
5. **Enable COD Payment** - Enables Cash on Delivery gateway for testing
6. **Create Products** - Creates 2 sample products:
   - Premium T-Shirt ($29.99)
   - Wireless Headphones ($79.99)
7. **Configure Permalinks** - Sets SEO-friendly URL structure
8. **Verify Setup** - Validates all components are working

### Exit Conditions

✅ **Success** - All checks pass, store ready for orders  
❌ **Failure** - Any verification fails, pod restarts (up to backoffLimit)

### Idempotency

The setup job is fully idempotent:
- Checks if WordPress is already installed
- Skips product creation if products exist
- Safe to re-run if job fails mid-execution

## Security Features

### Secrets Management

- All passwords auto-generated using `randAlphaNum`
- Secrets injected via `secretKeyRef` (not environment variables directly)
- No hardcoded credentials in source code
- Retrievable via kubectl for admin access

### Isolation

- Namespace-per-store model
- PVCs scoped to namespace
- Services use ClusterIP (internal only)
- Ingress exposes only HTTP endpoint

### Resource Limits

- CPU and memory limits prevent noisy neighbor issues
- Requests ensure guaranteed resources
- StorageClass quotas can be enforced at cluster level

## Testing End-to-End Order Flow

Once setup completes:

1. **Access storefront**: `http://{store.domain}` or `https://{store.domain}`
2. **Browse products**: See 2 sample products
3. **Add to cart**: Add a product to cart
4. **Checkout**: Proceed to checkout
5. **Payment**: Select "Cash on Delivery"
6. **Place order**: Complete order
7. **Verify in admin**: Login to `/wp-admin`, check WooCommerce → Orders
