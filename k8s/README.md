# Kubernetes Deployment for Glycol

This directory contains Kubernetes manifests for deploying the Glycol web interface to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.19+)
- `kubectl` configured to access your cluster
- Docker image built and available to your cluster
- OpenSky Network credentials (client_id and client_secret)

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t glycol-web:2.1.0 .

# Tag for your registry (if using a remote cluster)
docker tag glycol-web:2.1.0 your-registry.com/glycol-web:2.1.0

# Push to registry (if needed)
docker push your-registry.com/glycol-web:2.1.0
```

**For local clusters (minikube, kind, k3s):**
```bash
# Minikube
eval $(minikube docker-env)
docker build -t glycol-web:2.1.0 .

# kind
kind load docker-image glycol-web:2.1.0

# k3s - no special steps needed for local images
```

### 2. Configure Credentials

Edit `k8s/secret.yaml` and replace the placeholder credentials:

```yaml
stringData:
  credentials.json: |
    {
      "client_id": "your-actual-client-id",
      "client_secret": "your-actual-client-secret"
    }
```

**Alternative: Create secret from file**
```bash
kubectl create namespace glycol
kubectl create secret generic glycol-credentials \
  --from-file=credentials.json=./glycol/data/credentials.json \
  -n glycol
```

### 3. Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Optional: Apply ingress for external access
kubectl apply -f k8s/ingress.yaml
```

**Or apply all at once:**
```bash
kubectl apply -f k8s/
```

### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n glycol

# Check logs
kubectl logs -n glycol -l app=glycol-web -f

# Check service
kubectl get svc -n glycol

# Check health
kubectl exec -n glycol -it deploy/glycol-web -- wget -qO- http://localhost:5000/healthz/live
```

## Accessing the Application

### Port Forward (Development/Testing)

```bash
kubectl port-forward -n glycol svc/glycol-web 8666:80
```

Then open http://localhost:8666 in your browser.

### Via Ingress (Production)

1. Edit `k8s/ingress.yaml` and replace `glycol.example.com` with your domain
2. Configure DNS to point to your ingress controller's IP
3. Apply the ingress manifest:
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```
4. Access via https://glycol.example.com

## Configuration

### Change Image

Update `k8s/deployment.yaml`:
```yaml
spec:
  template:
    spec:
      containers:
      - name: glycol-web
        image: your-registry.com/glycol-web:2.1.0  # Change this
```

### Adjust Resources

Edit resource limits in `k8s/deployment.yaml`:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Scale Replicas

```bash
kubectl scale deployment glycol-web -n glycol --replicas=3
```

### Change Service Type

To expose directly via LoadBalancer (cloud environments):
```yaml
# k8s/service.yaml
spec:
  type: LoadBalancer  # Change from ClusterIP
```

## Health Checks

The deployment includes two health probes:

### Liveness Probe
- **Endpoint:** `/healthz/live`
- **Purpose:** Checks if app is running
- **Behavior:** Restarts pod if failing

### Readiness Probe
- **Endpoint:** `/healthz/ready`
- **Purpose:** Checks if app is authenticated and ready
- **Behavior:** Removes pod from service endpoints if failing

## Monitoring

### View Logs

```bash
# Follow logs
kubectl logs -n glycol -l app=glycol-web -f

# Logs from specific pod
kubectl logs -n glycol <pod-name> -f

# Previous container logs (if pod crashed)
kubectl logs -n glycol <pod-name> --previous
```

### Check Pod Status

```bash
kubectl get pods -n glycol
kubectl describe pod -n glycol <pod-name>
```

### Check Events

```bash
kubectl get events -n glycol --sort-by='.lastTimestamp'
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod -n glycol <pod-name>

# Check logs
kubectl logs -n glycol <pod-name>

# Check if secret exists
kubectl get secret -n glycol glycol-credentials
```

### Authentication Issues

```bash
# Check secret contents
kubectl get secret -n glycol glycol-credentials -o jsonpath='{.data.credentials\.json}' | base64 -d

# Check readiness probe
kubectl exec -n glycol -it deploy/glycol-web -- wget -qO- http://localhost:5000/healthz/ready
```

### Image Pull Errors

```bash
# For local clusters, make sure image is loaded
# Minikube:
eval $(minikube docker-env)
docker images | grep glycol

# kind:
docker exec -it kind-control-plane crictl images | grep glycol
```

### Health Check Failing

```bash
# Check liveness probe manually
kubectl exec -n glycol -it deploy/glycol-web -- wget -qO- http://localhost:5000/healthz/live

# Check readiness probe manually
kubectl exec -n glycol -it deploy/glycol-web -- wget -qO- http://localhost:5000/healthz/ready

# View probe status
kubectl describe pod -n glycol <pod-name> | grep -A 10 "Liveness\|Readiness"
```

## Advanced Configuration

### Persistent Logs

To persist logs across pod restarts, use a PersistentVolumeClaim:

```yaml
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: glycol-logs
  namespace: glycol
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

Then update `k8s/deployment.yaml`:
```yaml
volumes:
- name: logs
  persistentVolumeClaim:
    claimName: glycol-logs
```

### Resource Quotas

```yaml
# k8s/resourcequota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: glycol-quota
  namespace: glycol
spec:
  hard:
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
    pods: "5"
```

### Network Policies

```yaml
# k8s/networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: glycol-web-policy
  namespace: glycol
spec:
  podSelector:
    matchLabels:
      app: glycol-web
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 5000
  egress:
  - to:
    - namespaceSelector: {}
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 53  # DNS
```

## Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/

# Or delete namespace (removes everything)
kubectl delete namespace glycol
```

## Production Recommendations

1. **Use a private container registry** for your images
2. **Enable TLS/HTTPS** via ingress with cert-manager
3. **Set resource limits** appropriate for your workload
4. **Configure horizontal pod autoscaling** if needed
5. **Use secrets management** (Sealed Secrets, External Secrets, Vault)
6. **Enable monitoring** (Prometheus, Grafana)
7. **Configure network policies** for security
8. **Use RBAC** for access control
9. **Set up log aggregation** (Loki, ElasticSearch)
10. **Implement backup strategy** for persistent data

## Example: Complete Deployment

```bash
#!/bin/bash
# deploy.sh - Complete deployment script

set -e

NAMESPACE="glycol"
IMAGE="glycol-web:2.1.0"

echo "Building Docker image..."
docker build -t $IMAGE .

echo "Loading image to cluster..."
# Uncomment based on your cluster type
# kind load docker-image $IMAGE
# minikube image load $IMAGE

echo "Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "Creating secret..."
kubectl create secret generic glycol-credentials \
  --from-file=credentials.json=./glycol/data/credentials.json \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Deploying application..."
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

echo "Waiting for deployment..."
kubectl rollout status deployment/glycol-web -n $NAMESPACE

echo "Deployment complete!"
echo "Access via: kubectl port-forward -n $NAMESPACE svc/glycol-web 8666:80"
```

## License

Same as Glycol project (MIT)
