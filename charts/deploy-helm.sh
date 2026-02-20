#!/bin/bash
# deploy-helm.sh - Deploy Glycol using Helm

set -e

RELEASE_NAME="${1:-glycol}"
NAMESPACE="${2:-default}"
CLUSTER_TYPE="${3:-kind}"  # kind, minikube, k3s, or remote

echo "🎯 Deploying Glycol with Helm..."
echo "   Release: $RELEASE_NAME"
echo "   Namespace: $NAMESPACE"
echo "   Cluster type: $CLUSTER_TYPE"
echo ""

# Build Docker image
echo "📦 Building Docker image..."
docker build -t glycol-web:2.2.0 ..

# Load image to cluster (for local clusters)
if [ "$CLUSTER_TYPE" = "kind" ]; then
    echo "📥 Loading image to kind cluster..."
    kind load docker-image glycol-web:2.2.0
elif [ "$CLUSTER_TYPE" = "minikube" ]; then
    echo "📥 Loading image to minikube..."
    minikube image load glycol-web:2.2.0
elif [ "$CLUSTER_TYPE" = "k3s" ]; then
    echo "📥 Image available locally for k3s..."
else
    echo "⚠️  Remote cluster detected - ensure image is pushed to registry"
fi

# Check for credentials
if [ -f "../glycol/data/credentials.json" ]; then
    echo "🔐 Found credentials file"
    CLIENT_ID=$(jq -r '.client_id' ../glycol/data/credentials.json)
    CLIENT_SECRET=$(jq -r '.client_secret' ../glycol/data/credentials.json)

    if [ "$CLIENT_ID" = "null" ] || [ "$CLIENT_SECRET" = "null" ]; then
        echo "⚠️  Warning: credentials.json found but missing client_id or client_secret"
        echo "   You'll need to provide them via --set or update the file"
        CREDS_ARGS=""
    else
        CREDS_ARGS="--set credentials.clientId=$CLIENT_ID --set credentials.clientSecret=$CLIENT_SECRET"
    fi
else
    echo "⚠️  No credentials file found at ../glycol/data/credentials.json"
    echo "   You'll need to provide credentials via --set or create the file"
    CREDS_ARGS=""
fi

# Create namespace if it doesn't exist
if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    echo "📂 Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
fi

# Install or upgrade with Helm
echo "🚀 Installing/upgrading Helm release..."
if helm status "$RELEASE_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
    echo "   Upgrading existing release..."
    helm upgrade "$RELEASE_NAME" ./glycol \
        --namespace "$NAMESPACE" \
        $CREDS_ARGS \
        --wait \
        --timeout 5m
else
    echo "   Installing new release..."
    helm install "$RELEASE_NAME" ./glycol \
        --namespace "$NAMESPACE" \
        --create-namespace \
        $CREDS_ARGS \
        --wait \
        --timeout 5m
fi

# Get release status
echo ""
echo "📊 Release status:"
helm status "$RELEASE_NAME" -n "$NAMESPACE"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "   # View logs"
echo "   kubectl logs -n $NAMESPACE -l app.kubernetes.io/name=glycol -f"
echo ""
echo "   # Port forward to access"
echo "   kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME 8666:80"
echo "   # Then open http://localhost:8666"
echo ""
echo "   # Check health"
echo "   kubectl exec -n $NAMESPACE -it deploy/$RELEASE_NAME -- wget -qO- http://localhost:8666/healthz/ready"
echo ""
echo "   # Uninstall"
echo "   helm uninstall $RELEASE_NAME -n $NAMESPACE"
echo ""
