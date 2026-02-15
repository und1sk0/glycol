#!/bin/bash
# deploy.sh - Deploy Glycol to Kubernetes cluster

set -e

NAMESPACE="glycol"
IMAGE="glycol-web:2.1.0"
CLUSTER_TYPE="${1:-kind}"  # kind, minikube, or remote

echo "🚀 Deploying Glycol to Kubernetes..."
echo "   Namespace: $NAMESPACE"
echo "   Image: $IMAGE"
echo "   Cluster type: $CLUSTER_TYPE"
echo ""

# Build Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE ..

# Load image to cluster (for local clusters)
if [ "$CLUSTER_TYPE" = "kind" ]; then
    echo "📥 Loading image to kind cluster..."
    kind load docker-image $IMAGE
elif [ "$CLUSTER_TYPE" = "minikube" ]; then
    echo "📥 Loading image to minikube..."
    minikube image load $IMAGE
elif [ "$CLUSTER_TYPE" = "k3s" ]; then
    echo "📥 Image available locally for k3s..."
else
    echo "⚠️  Remote cluster detected - ensure image is pushed to registry"
fi

# Create namespace
echo "📂 Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create secret from local credentials file
if [ -f "../glycol/data/credentials.json" ]; then
    echo "🔐 Creating secret from credentials file..."
    kubectl create secret generic glycol-credentials \
      --from-file=credentials.json=../glycol/data/credentials.json \
      -n $NAMESPACE \
      --dry-run=client -o yaml | kubectl apply -f -
else
    echo "⚠️  Credentials file not found at ../glycol/data/credentials.json"
    echo "   Applying secret.yaml (make sure to update with real credentials first)"
    kubectl apply -f secret.yaml
fi

# Deploy application
echo "🎯 Deploying application..."
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/glycol-web -n $NAMESPACE --timeout=5m

# Check health
echo "🏥 Checking health..."
POD=$(kubectl get pods -n $NAMESPACE -l app=glycol-web -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n $NAMESPACE $POD -- wget -qO- http://localhost:5000/healthz/live | jq . || true

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Access the application:"
echo "   kubectl port-forward -n $NAMESPACE svc/glycol-web 8666:80"
echo "   Then open http://localhost:8666"
echo ""
echo "View logs:"
echo "   kubectl logs -n $NAMESPACE -l app=glycol-web -f"
echo ""
echo "Check status:"
echo "   kubectl get pods -n $NAMESPACE"
echo ""
