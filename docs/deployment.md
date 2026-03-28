# Guía de Despliegue - Plataforma de Telemedicina

## Requisitos Previos

### Infraestructura
- Kubernetes (K3s, EKS, GKE o AKS)
- Helm 3.x
- kubectl configurado
- Cert-manager para TLS
- Ingress controller (Traefik o Nginx)

### Recursos Mínimos
- 8 vCPUs
- 16 GB RAM
- 50 GB Storage

## Preparación del Entorno

### 1. Crear namespace
```bash
kubectl create namespace telemedicina
```

### 2. Instalar dependencias
```bash
# Helm repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Ingress (Traefik)
helm install traefik traefik/traefik -n ingress
```

### 3. Configurar secrets
```bash
kubectl create secret generic telemedicina-secrets \
  --from-literal=POSTGRES_PASSWORD=your-secure-password \
  --from-literal=JWT_SECRET=your-jwt-secret \
  --from-literal=LIVEKIT_API_SECRET=your-livekit-secret \
  -n telemedicina
```

## Despliegue con Helm

### Desarrollo Local
```bash
# Usando kind o minikube
helm install dev ./charts/telemedicina -f ./charts/telemedicina/values.yaml -n telemedicina
```

### Producción
```bash
# Crear values personalizado
cp charts/telemedicina/values.yaml values-prod.yaml

# Editar con configuraciones de producción
vim values-prod.yaml

# Desplegar
helm install prod ./charts/telemedicina -f values-prod.yaml -n telemedicina
```

## Verificación

### 1. Verificar pods
```bash
kubectl get pods -n telemedicina
```

### 2. Verificar servicios
```bash
kubectl get svc -n telemedicina
```

### 3. Verificar ingress
```bash
kubectl get ingress -n telemedicina
```

### 4. Health checks
```bash
# Backend
curl https://api.telemedicina.com/health

# Frontend
curl https://app.telemedicina.com

# LiveKit
curl https://livekit.telemedicina.com/health
```

## Monitoreo

### Acceder a Grafana
```bash
# Obtener password
kubectl get secret grafana -o jsonpath='{.data.admin-password}' | base64 -d

# Port forward
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

### Dashboards
- LiveKit: Métricas de rooms y participantes
- Backend: Solicitudes, latencia, errores
- Postgres: Queries lentas, conexiones
- Redis: Memoria, hits/misses

## Escalado

### Horizontal
```bash
kubectl scale deployment backend --replicas=5 -n telemedicina
```

### Vertical
```bash
kubectl patch deployment backend -p '{"spec":{"template":{"spec":{"containers":[{"name":"backend","resources":{"limits":{"cpu":"2","memory":"2Gi"}}]}}}}' -n telemedicina
```

## Backup y Restauración

### PostgreSQL
```bash
# Backup
kubectl exec -n telemedicina deploy/postgres -- pg_dump -U telemedicina telemedicina > backup.sql

# Restaurar
kubectl exec -i -n telemedicina deploy/postgres -- psql -U telemedicina telemedicina < backup.sql
```

### MinIO (Grabaciones)
```bash
# Usar mc CLI
mc mirror minio/data/recordings /local/backups/recordings/
```

## Troubleshooting

### Ver logs
```bash
kubectl logs -n telemedicina deployment/backend
kubectl logs -n telemedicina deployment/frontend
kubectl logs -n telemedicina statefulset/livekit
```

### Reiniciar pods
```bash
kubectl rollout restart deployment -n telemedicina
```

### Ver eventos
```bash
kubectl get events -n telemedicina --sort-by='.lastTimestamp'
```

## Limpieza

```bash
# Desinstalar
helm uninstall prod -n telemedicina

# Eliminar namespace
kubectl delete namespace telemedicina
```
