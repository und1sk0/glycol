# Docker Deployment for Glycol Web Interface

This guide covers running the Glycol web interface in a Docker container.

## Quick Start

### Prerequisites

- Docker installed
- OpenSky Network credentials configured in `glycol/data/credentials.json`

### Build the Image

```bash
docker build -t glycol-web:2.1.0 .
```

### Run the Container

```bash
docker run -d \
  --name glycol-web \
  -p 8666:8666 \
  -v $(pwd)/glycol/data/credentials.json:/app/glycol/data/credentials.json:ro \
  -v $(pwd)/logs:/app/logs \
  glycol-web:2.1.0
```

Then open your browser to http://localhost:8666

## Using Docker Compose

The easiest way to run Glycol is with Docker Compose:

```bash
# Start the service
docker compose up -d

# View logs
docker compose logs -f

# Stop the service
docker compose down
```

## Configuration

### Port Configuration

Change the port via environment variable:

```bash
# Using Docker run
docker run -d \
  --name glycol-web \
  -p 8080:8666 \
  -e PORT=8666 \
  -v $(pwd)/glycol/data/credentials.json:/app/glycol/data/credentials.json:ro \
  glycol-web:2.1.0

# Using Docker Compose
PORT=8080 docker compose up -d
```

### Custom Port in Container

To run on a different port inside the container:

```bash
docker run -d \
  --name glycol-web \
  -p 8080:8080 \
  -v $(pwd)/glycol/data/credentials.json:/app/glycol/data/credentials.json:ro \
  glycol-web:2.1.0 \
  --host 0.0.0.0 --port 8080
```

## Volume Mounts

### Required Volumes

- **Credentials** (required): Mount your OpenSky credentials
  ```bash
  -v $(pwd)/glycol/data/credentials.json:/app/glycol/data/credentials.json:ro
  ```

### Optional Volumes

- **Logs**: Persist logs outside the container
  ```bash
  -v $(pwd)/logs:/app/logs
  ```

- **Data**: Use custom aircraft database or type groups
  ```bash
  -v $(pwd)/glycol/data:/app/glycol/data:ro
  ```

## Multi-Stage Build

The Dockerfile uses a multi-stage build for minimal image size:

- **Stage 1 (builder)**: Compiles Python dependencies with build tools
- **Stage 2 (runtime)**: Copies only the runtime environment
- **Base**: Alpine Linux with Python 3.13
- **Result**: Stripped-down image (~150MB vs ~1GB for full Python)

### Build Arguments

Build with custom Python version:

```bash
docker build \
  --build-arg PYTHON_VERSION=3.12 \
  -t glycol-web:2.1.0 \
  .
```

## Health Checks

The container includes health check endpoints for monitoring:

### Endpoints

- **`/healthz/live`** - Liveness probe (always returns 200 if app is running)
- **`/healthz/ready`** or **`/healthz`** - Readiness probe (returns 200 only if authenticated)

### Docker Health Check

The Dockerfile includes a built-in health check using the liveness endpoint:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' glycol-web

# View health check logs
docker inspect --format='{{json .State.Health}}' glycol-web | jq
```

### Manual Health Checks

```bash
# Liveness check (should always return 200)
curl http://localhost:8666/healthz/live

# Readiness check (returns 200 if authenticated, 503 if not)
curl http://localhost:8666/healthz/ready
curl http://localhost:8666/healthz
```

## Security

### Non-Root User

The container runs as non-root user `glycol` (UID 1000) for security.

### Read-Only Credentials

Mount credentials as read-only (`:ro`) to prevent accidental modification:

```bash
-v $(pwd)/glycol/data/credentials.json:/app/glycol/data/credentials.json:ro
```

## Networking

### Access from Host Only

Default configuration (localhost only):

```bash
docker run -d -p 127.0.0.1:8666:8666 ... glycol-web:2.1.0
```

### Access from Network

Allow access from other devices:

```bash
docker run -d -p 0.0.0.0:8666:8666 ... glycol-web:2.1.0
```

## Troubleshooting

### View Logs

```bash
# Container logs
docker logs -f glycol-web

# Application logs (if mounted)
tail -f logs/glycol-*.log
```

### Interactive Shell

```bash
docker exec -it glycol-web sh
```

### Rebuild from Scratch

```bash
docker build --no-cache -t glycol-web:2.1.0 .
```

### Check Environment

```bash
docker exec glycol-web env
```

## Image Size

The multi-stage Alpine build produces a minimal image:

```bash
docker images glycol-web
# REPOSITORY    TAG       SIZE
# glycol-web    2.0.0     ~150MB
```

Compare to standard Python image: ~1GB

## Production Deployment

For production, consider:

1. **Use a reverse proxy** (nginx, Traefik) for HTTPS
2. **Set resource limits**:
   ```bash
   docker run -d \
     --memory="512m" \
     --cpus="1.0" \
     ... glycol-web:2.1.0
   ```
3. **Enable auto-restart**:
   ```bash
   docker run -d --restart=unless-stopped ... glycol-web:2.1.0
   ```
4. **Monitor with health checks**
5. **Use Docker secrets** for credentials in Swarm/Kubernetes

## Examples

### Run on Custom Port 8080

```bash
docker run -d \
  --name glycol-web \
  -p 8080:8080 \
  -v $(pwd)/glycol/data/credentials.json:/app/glycol/data/credentials.json:ro \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  glycol-web:2.1.0 \
  --host 0.0.0.0 --port 8080
```

### Development with Live Reload

Mount the code directory for development:

```bash
docker run -d \
  --name glycol-dev \
  -p 8666:8666 \
  -v $(pwd)/glycol:/app/glycol \
  -v $(pwd)/glycol/data/credentials.json:/app/glycol/data/credentials.json:ro \
  glycol-web:2.1.0
```

## Kubernetes Deployment

### Example Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: glycol-web
  labels:
    app: glycol-web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: glycol-web
  template:
    metadata:
      labels:
        app: glycol-web
    spec:
      containers:
      - name: glycol-web
        image: glycol-web:2.1.0
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: PORT
          value: "5000"
        - name: HOST
          value: "0.0.0.0"
        volumeMounts:
        - name: credentials
          mountPath: /app/glycol/data/credentials.json
          subPath: credentials.json
          readOnly: true
        - name: logs
          mountPath: /app/logs
        livenessProbe:
          httpGet:
            path: /healthz/live
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /healthz/ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: credentials
        secret:
          secretName: glycol-credentials
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: glycol-web
spec:
  selector:
    app: glycol-web
  ports:
  - port: 80
    targetPort: 5000
    name: http
  type: ClusterIP
```

### Create Kubernetes Secret for Credentials

```bash
# Create secret from credentials file
kubectl create secret generic glycol-credentials \
  --from-file=credentials.json=glycol/data/credentials.json

# Or create from literal values
kubectl create secret generic glycol-credentials \
  --from-literal=credentials.json='{"client_id":"your-id","client_secret":"your-secret"}'
```

### Deploy to Kubernetes

```bash
# Apply the manifest
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=glycol-web
kubectl get svc glycol-web

# View logs
kubectl logs -l app=glycol-web -f

# Port forward to test locally
kubectl port-forward svc/glycol-web 8666:80
```

### Ingress Example

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: glycol-web
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - glycol.example.com
    secretName: glycol-tls
  rules:
  - host: glycol.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: glycol-web
            port:
              number: 80
```

## License

Same as Glycol project (MIT)
