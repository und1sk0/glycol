# Glycol Helm Chart

A Helm chart for deploying Glycol - a real-time airport flight monitoring application using the OpenSky Network API.

## TL;DR

```bash
# Build the Docker image
docker build -t glycol-web:2.1.0 .

# Install the chart with credentials
helm install glycol ./charts/glycol \
  --set credentials.clientId=YOUR_CLIENT_ID \
  --set credentials.clientSecret=YOUR_CLIENT_SECRET

# Access the application
kubectl port-forward svc/glycol 8666:80
# Open http://localhost:8666
```

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- Docker image built and available to your cluster
- OpenSky Network API credentials ([get them here](https://opensky-network.org/))

## Installing the Chart

### Option 1: Install with inline credentials

```bash
helm install glycol ./charts/glycol \
  --set credentials.clientId=YOUR_CLIENT_ID \
  --set credentials.clientSecret=YOUR_CLIENT_SECRET
```

### Option 2: Install with existing secret

```bash
# Create secret
kubectl create secret generic glycol-creds \
  --from-literal=credentials.json='{"client_id":"xxx","client_secret":"yyy"}'

# Install chart
helm install glycol ./charts/glycol \
  --set credentials.existingSecret=glycol-creds
```

### Option 3: Install with custom values file

```bash
# Create values-prod.yaml
cat > values-prod.yaml <<EOF
credentials:
  clientId: "your-client-id"
  clientSecret: "your-client-secret"

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: glycol.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: glycol-tls
      hosts:
        - glycol.yourdomain.com

persistence:
  enabled: true
  size: 2Gi

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi
EOF

# Install with custom values
helm install glycol ./charts/glycol -f values-prod.yaml
```

## Uninstalling the Chart

```bash
helm uninstall glycol
```

This removes all the Kubernetes components associated with the chart and deletes the release.

## Configuration

The following table lists the configurable parameters of the Glycol chart and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of Glycol replicas | `1` |
| `image.repository` | Image repository | `glycol-web` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `image.tag` | Image tag (overrides chart appVersion) | `""` |
| `imagePullSecrets` | Docker registry secret names | `[]` |
| `nameOverride` | String to partially override chart name | `""` |
| `fullnameOverride` | String to fully override chart name | `""` |

### Credentials

| Parameter | Description | Default |
|-----------|-------------|---------|
| `credentials.clientId` | OpenSky Network client ID | `""` |
| `credentials.clientSecret` | OpenSky Network client secret | `""` |
| `credentials.existingSecret` | Name of existing secret with credentials | `""` |
| `credentials.existingSecretKey` | Key in existing secret containing credentials.json | `credentials.json` |

### Service Account

| Parameter | Description | Default |
|-----------|-------------|---------|
| `serviceAccount.create` | Create service account | `true` |
| `serviceAccount.automount` | Automount service account token | `true` |
| `serviceAccount.annotations` | Service account annotations | `{}` |
| `serviceAccount.name` | Service account name | `""` |

### Security

| Parameter | Description | Default |
|-----------|-------------|---------|
| `podSecurityContext.runAsNonRoot` | Run as non-root user | `true` |
| `podSecurityContext.runAsUser` | User ID to run as | `1000` |
| `podSecurityContext.fsGroup` | Group ID for volumes | `1000` |
| `securityContext.capabilities.drop` | Linux capabilities to drop | `["ALL"]` |
| `securityContext.readOnlyRootFilesystem` | Mount root filesystem as read-only | `false` |
| `securityContext.allowPrivilegeEscalation` | Allow privilege escalation | `false` |

### Service

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.port` | Service port | `80` |
| `service.targetPort` | Container port | `8666` |

### Ingress

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.annotations` | Ingress annotations | `{}` |
| `ingress.hosts` | Ingress hostnames and paths | See `values.yaml` |
| `ingress.tls` | Ingress TLS configuration | `[]` |

### Resources

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `250m` |
| `resources.requests.memory` | Memory request | `256Mi` |

### Health Checks

| Parameter | Description | Default |
|-----------|-------------|---------|
| `livenessProbe.httpGet.path` | Liveness probe path | `/healthz/live` |
| `livenessProbe.initialDelaySeconds` | Initial delay | `10` |
| `livenessProbe.periodSeconds` | Check interval | `30` |
| `readinessProbe.httpGet.path` | Readiness probe path | `/healthz/ready` |
| `readinessProbe.initialDelaySeconds` | Initial delay | `5` |
| `readinessProbe.periodSeconds` | Check interval | `10` |

### Autoscaling

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `5` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU % | `80` |
| `autoscaling.targetMemoryUtilizationPercentage` | Target memory % | `80` |

### Persistence

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistent storage for logs | `false` |
| `persistence.storageClass` | Storage class | `""` |
| `persistence.accessMode` | Access mode | `ReadWriteOnce` |
| `persistence.size` | Volume size | `1Gi` |
| `persistence.existingClaim` | Use existing PVC | `""` |

### Application Config

| Parameter | Description | Default |
|-----------|-------------|---------|
| `config.port` | Flask app port | `8666` |
| `config.host` | Flask app host | `0.0.0.0` |
| `config.pythonUnbuffered` | Python buffering | `"1"` |

### Other

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nodeSelector` | Node labels for pod assignment | `{}` |
| `tolerations` | Tolerations for pod assignment | `[]` |
| `affinity` | Affinity rules for pod assignment | `{}` |
| `extraEnv` | Additional environment variables | `[]` |
| `volumes` | Additional volumes | `[]` |
| `volumeMounts` | Additional volume mounts | `[]` |

## Examples

### Enable Ingress with TLS

```yaml
# values-ingress.yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: glycol.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: glycol-tls
      hosts:
        - glycol.example.com
```

```bash
helm install glycol ./charts/glycol -f values-ingress.yaml
```

### Enable Autoscaling

```yaml
# values-hpa.yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

```bash
helm install glycol ./charts/glycol -f values-hpa.yaml
```

### Enable Persistent Logs

```yaml
# values-persistence.yaml
persistence:
  enabled: true
  size: 5Gi
  storageClass: standard
```

```bash
helm install glycol ./charts/glycol -f values-persistence.yaml
```

### Use LoadBalancer Service

```yaml
# values-loadbalancer.yaml
service:
  type: LoadBalancer
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
```

```bash
helm install glycol ./charts/glycol -f values-loadbalancer.yaml
```

### Production Configuration

```yaml
# values-production.yaml
replicaCount: 3

image:
  repository: registry.example.com/glycol-web
  tag: "2.1.0"
  pullPolicy: Always

imagePullSecrets:
  - name: registry-credentials

credentials:
  existingSecret: glycol-credentials

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: glycol.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: glycol-tls
      hosts:
        - glycol.example.com

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

persistence:
  enabled: true
  size: 10Gi
  storageClass: fast-ssd

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8666"
  prometheus.io/path: "/metrics"

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app.kubernetes.io/name
                operator: In
                values:
                  - glycol
          topologyKey: kubernetes.io/hostname
```

```bash
helm install glycol ./charts/glycol -f values-production.yaml
```

## Upgrading

### Upgrade with new credentials

```bash
helm upgrade glycol ./charts/glycol \
  --set credentials.clientId=NEW_CLIENT_ID \
  --set credentials.clientSecret=NEW_CLIENT_SECRET
```

### Upgrade with new values file

```bash
helm upgrade glycol ./charts/glycol -f values-new.yaml
```

### Upgrade image version

```bash
helm upgrade glycol ./charts/glycol \
  --set image.tag=2.2.0
```

## Troubleshooting

### Check pod status

```bash
kubectl get pods -l app.kubernetes.io/name=glycol
kubectl describe pod -l app.kubernetes.io/name=glycol
```

### View logs

```bash
kubectl logs -l app.kubernetes.io/name=glycol -f
```

### Check health endpoints

```bash
# Liveness
kubectl exec -it deploy/glycol -- wget -qO- http://localhost:8666/healthz/live

# Readiness
kubectl exec -it deploy/glycol -- wget -qO- http://localhost:8666/healthz/ready
```

### Debug configuration

```bash
# View rendered templates
helm template glycol ./charts/glycol

# View all values
helm get values glycol

# View computed values
helm get values glycol --all
```

## Development

### Linting

```bash
helm lint ./charts/glycol
```

### Testing

```bash
# Dry run
helm install glycol ./charts/glycol --dry-run --debug

# Template rendering
helm template glycol ./charts/glycol

# Install in test namespace
helm install glycol-test ./charts/glycol \
  --namespace glycol-test \
  --create-namespace \
  --set credentials.clientId=test \
  --set credentials.clientSecret=test
```

### Packaging

```bash
# Package the chart
helm package ./charts/glycol

# This creates glycol-0.1.0.tgz
```

## License

MIT - Same as Glycol project
