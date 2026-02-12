# Quick Start Guide - Helm Chart Testing

This guide helps you quickly test the Helm chart in a local Kubernetes environment.

## Prerequisites

1. **Docker Desktop** (with Kubernetes enabled) OR **kind/minikube**
2. **Helm 3.x** installed
3. **kubectl** installed and configured

## Step 1: Verify Prerequisites

```bash
# Check Kubernetes is running
kubectl cluster-info

# Check Helm is installed
helm version

# Check current context
kubectl config current-context
```

## Step 2: Install NGINX Ingress Controller (if not already installed)

### For Docker Desktop Kubernetes:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

### For kind:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/kind/deploy.yaml
```

### For minikube:
```bash
minikube addons enable ingress
```

### Verify ingress controller is running:
```bash
kubectl get pods -n ingress-nginx
```

## Step 3: Validate the Helm Chart

```bash
# Navigate to project root
cd "d:\Internship\Urumi AI\GenAI SDE Task SPP\store-provisioning-platform"

# Run validation script (PowerShell)
.\helm\validate-chart.ps1

# OR manually lint the chart
helm lint ./helm/store
```

## Step 4: Install a Test Store

```bash
# Install WooCommerce store
helm install store-test123 ./helm/store \
  --namespace store-test123 \
  --create-namespace \
  -f ./helm/store/values.yaml \
  -f ./helm/store/values-local.yaml \
  --set store.id=test123 \
  --set store.name="My Test Store" \
  --set store.namespace=store-test123 \
  --set store.engine=woocommerce \
  --set store.domain=test.localhost
```

## Step 5: Monitor Setup Progress

```bash
# Watch all pods in the namespace
kubectl get pods -n store-test123 -w

# In another terminal, follow setup job logs
kubectl logs -n store-test123 job/store-test123-woocommerce-setup -f

# Check setup job status
kubectl get job -n store-test123
```

**Expected timeline:**
- MySQL pod ready: ~30-60 seconds
- WordPress pod ready: ~60-90 seconds
- Setup job completes: ~2-3 minutes total

## Step 6: Verify Installation

```bash
# Check all resources
kubectl get all -n store-test123

# Check PVCs
kubectl get pvc -n store-test123

# Check secrets
kubectl get secrets -n store-test123

# Check ingress
kubectl get ingress -n store-test123
```

## Step 7: Access the Store

### Add to hosts file (Windows):

1. Open PowerShell as Administrator:
```powershell
notepad C:\Windows\System32\drivers\etc\hosts
```

2. Add this line:
```
127.0.0.1 test.localhost
```

3. Save and close

### Access URLs:

- **Storefront**: http://test.localhost
- **Admin**: http://test.localhost/wp-admin

### Get Admin Password:

```bash
# PowerShell
kubectl get secret store-test123-admin-credentials -n store-test123 -o jsonpath='{.data.WORDPRESS_ADMIN_PASSWORD}' | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }

# Or on Linux/Mac
kubectl get secret store-test123-admin-credentials -n store-test123 -o jsonpath='{.data.WORDPRESS_ADMIN_PASSWORD}' | base64 -d
```

**Default admin username**: `admin`

## Step 8: Test Order Placement

1. Open http://test.localhost in browser
2. Browse available products (Premium T-Shirt, Wireless Headphones)
3. Click "Add to cart" on any product
4. View cart and proceed to checkout
5. Fill in billing details (any test data is fine)
6. Select payment method: **Cash on Delivery**
7. Place order
8. Verify order appears in admin panel:
   - Login to http://test.localhost/wp-admin
   - Navigate to WooCommerce → Orders
   - Confirm your order is listed

✅ **Success!** You've placed an end-to-end order.

## Step 9: Inspect Resources (Optional)

```bash
# Get detailed pod info
kubectl describe pod -n store-test123 -l app.kubernetes.io/component=wordpress

# Check MySQL logs
kubectl logs -n store-test123 -l app.kubernetes.io/component=mysql

# Check WordPress logs
kubectl logs -n store-test123 -l app.kubernetes.io/component=wordpress

# Execute commands inside WordPress pod
kubectl exec -it -n store-test123 deployment/store-test123-wordpress -- bash

# Inside the pod:
wp plugin list --allow-root --path=/var/www/html
wp wc product list --allow-root --path=/var/www/html
```

## Step 10: Cleanup

```bash
# Uninstall the Helm release
helm uninstall store-test123 -n store-test123

# Delete the namespace (and all PVCs)
kubectl delete namespace store-test123

# Verify cleanup
kubectl get all -n store-test123
# Should return: No resources found in store-test123 namespace (or namespace not found)
```

## Troubleshooting

### Setup Job Fails

```bash
# Check setup job logs
kubectl logs -n store-test123 job/store-test123-woocommerce-setup

# Check job events
kubectl describe job -n store-test123 store-test123-woocommerce-setup
```

**Common issues:**
- WordPress pod not ready → Check WordPress logs
- MySQL connection failure → Check MySQL pod status
- Timeout waiting for WordPress → Increase wait time in values

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod -n store-test123 <pod-name>
```

**Common issues:**
- `ImagePullBackOff` → Check internet connection
- `Pending` PVC → Check if StorageClass exists:
  ```bash
  kubectl get storageclass
  ```
  If none exist, create one or use `hostPath` provisioner

### Ingress Not Working

```bash
# Check ingress status
kubectl get ingress -n store-test123

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

**Common issues:**
- Ingress controller not installed → Install as per Step 2
- Domain not resolving → Check hosts file
- Port 80 not forwarded → Check Docker Desktop settings

### Cannot Access http://test.localhost

1. Verify ingress is created:
   ```bash
   kubectl get ingress -n store-test123
   ```

2. Check ingress controller is running:
   ```bash
   kubectl get pods -n ingress-nginx
   ```

3. Verify hosts file entry:
   ```
   127.0.0.1 test.localhost
   ```

4. Try accessing via port-forward as fallback:
   ```bash
   kubectl port-forward -n store-test123 service/store-test123-wordpress 8080:80
   ```
   Then access: http://localhost:8080

## Testing Multiple Stores

Install a second store with different values:

```bash
helm install store-demo456 ./helm/store \
  --namespace store-demo456 \
  --create-namespace \
  -f ./helm/store/values.yaml \
  -f ./helm/store/values-local.yaml \
  --set store.id=demo456 \
  --set store.name="Demo Store" \
  --set store.namespace=store-demo456 \
  --set store.engine=woocommerce \
  --set store.domain=demo.localhost

# Add to hosts file:
# 127.0.0.1 demo.localhost

# Access at: http://demo.localhost
```

**Key takeaway**: Each store is completely isolated in its own namespace with its own resources.

## Upgrade Testing

Modify a value and upgrade:

```bash
# Upgrade with increased resources
helm upgrade store-test123 ./helm/store \
  --namespace store-test123 \
  -f ./helm/store/values.yaml \
  -f ./helm/store/values-local.yaml \
  --set store.id=test123 \
  --set store.name="My Test Store (UPGRADED)" \
  --set store.namespace=store-test123 \
  --set store.engine=woocommerce \
  --set store.domain=test.localhost \
  --set woocommerce.wordpress.resources.limits.memory=1Gi

# Check revision history
helm history store-test123 -n store-test123

# Rollback if needed
helm rollback store-test123 -n store-test123
```

## Production Testing (k3s on VPS)

If you have a VPS with k3s:

```bash
# Use production values
helm install store-prod789 ./helm/store \
  --namespace store-prod789 \
  --create-namespace \
  -f ./helm/store/values.yaml \
  -f ./helm/store/values-prod.yaml \
  --set store.id=prod789 \
  --set store.name="Production Store" \
  --set store.namespace=store-prod789 \
  --set store.engine=woocommerce \
  --set store.domain=store.yourdomain.com

# Note: Requires:
# - DNS A record pointing to VPS IP
# - cert-manager installed for TLS
# - StorageClass configured
```

## Success Criteria

✅ Helm chart installs without errors  
✅ All pods reach Ready state  
✅ Setup job completes successfully  
✅ Storefront accessible via ingress  
✅ Admin login works  
✅ Products are visible  
✅ Can add product to cart  
✅ Can complete checkout with COD  
✅ Order appears in WooCommerce admin  
✅ Helm uninstall removes all resources cleanly  

## Next Steps

After successful testing:

1. **Integrate with backend** - Backend calls `helm install` with dynamic values
2. **Test backend provisioning** - Backend orchestrates store creation
3. **Test dashboard** - View stores in React dashboard
4. **Test deletion** - Backend calls `helm uninstall`
5. **Performance testing** - Create multiple stores concurrently
6. **Production deployment** - Deploy to k3s VPS

---

**Need Help?**

- Check [helm/README.md](README.md) for detailed documentation
- Check [helm/IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture details
- Review NOTES.txt after installation for troubleshooting tips
