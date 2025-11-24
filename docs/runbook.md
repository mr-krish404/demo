# Apex Pentest X - Operations Runbook

## Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Docker registry access
- Secrets configured

### Initial Deployment

1. **Create namespace:**
```bash
kubectl apply -f infra/k8s/namespace.yaml
```

2. **Create secrets:**
```bash
kubectl create secret generic apex-secrets \
  --from-literal=postgres-user=apex_user \
  --from-literal=postgres-password=SECURE_PASSWORD \
  --from-literal=database-url=postgresql://apex_user:SECURE_PASSWORD@postgres:5432/apex_pentest \
  --from-literal=jwt-secret=RANDOM_SECRET_KEY \
  --from-literal=minio-access-key=apex_minio \
  --from-literal=minio-secret-key=SECURE_PASSWORD \
  --from-literal=gemini-api-key=YOUR_API_KEY \
  -n apex-pentest
```

3. **Deploy infrastructure:**
```bash
kubectl apply -f infra/k8s/postgres-deployment.yaml
kubectl apply -f infra/k8s/redis-deployment.yaml
```

4. **Deploy services:**
```bash
kubectl apply -f infra/k8s/gateway-deployment.yaml
kubectl apply -f infra/k8s/orchestrator-deployment.yaml
```

5. **Verify deployment:**
```bash
kubectl get pods -n apex-pentest
kubectl get services -n apex-pentest
```

### Local Development

1. **Start infrastructure:**
```bash
cd infra/docker
docker-compose up -d
```

2. **Start backend services:**
```bash
cd services/gateway
poetry install
poetry run uvicorn app.main:app --reload --port 8080

cd services/orchestrator
poetry install
poetry run uvicorn app.main:app --reload --port 8081
```

3. **Start frontend:**
```bash
cd ui/web
npm install
npm run dev
```

## Monitoring

### Health Checks

**Gateway:**
```bash
curl http://localhost:8080/health
```

**Orchestrator:**
```bash
curl http://localhost:8081/health
```

### Logs

**View pod logs:**
```bash
kubectl logs -f deployment/gateway -n apex-pentest
kubectl logs -f deployment/orchestrator -n apex-pentest
```

**View agent logs:**
```bash
kubectl logs -f -l app=agent-runner -n apex-pentest
```

### Metrics

**Check resource usage:**
```bash
kubectl top pods -n apex-pentest
kubectl top nodes
```

## Troubleshooting

### Common Issues

#### 1. Pods not starting

**Check pod status:**
```bash
kubectl describe pod <pod-name> -n apex-pentest
```

**Common causes:**
- Image pull errors
- Missing secrets
- Resource constraints
- Failed health checks

**Solution:**
```bash
# Check events
kubectl get events -n apex-pentest --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n apex-pentest
```

#### 2. Database connection errors

**Check PostgreSQL:**
```bash
kubectl exec -it deployment/postgres -n apex-pentest -- psql -U apex_user -d apex_pentest
```

**Verify connection string:**
```bash
kubectl get secret apex-secrets -n apex-pentest -o jsonpath='{.data.database-url}' | base64 -d
```

#### 3. Agent execution failures

**Check agent runner logs:**
```bash
kubectl logs deployment/agent-runner -n apex-pentest
```

**Verify Docker socket access:**
```bash
kubectl exec -it deployment/agent-runner -n apex-pentest -- docker ps
```

#### 4. High memory usage

**Check memory usage:**
```bash
kubectl top pods -n apex-pentest
```

**Scale down if needed:**
```bash
kubectl scale deployment gateway --replicas=2 -n apex-pentest
```

## Backup & Recovery

### Database Backup

**Create backup:**
```bash
kubectl exec deployment/postgres -n apex-pentest -- pg_dump -U apex_user apex_pentest > backup.sql
```

**Restore backup:**
```bash
kubectl exec -i deployment/postgres -n apex-pentest -- psql -U apex_user apex_pentest < backup.sql
```

### Evidence Storage Backup

**Backup MinIO data:**
```bash
kubectl exec deployment/minio -n apex-pentest -- mc mirror /data /backup
```

## Scaling

### Manual Scaling

**Scale gateway:**
```bash
kubectl scale deployment gateway --replicas=5 -n apex-pentest
```

**Scale orchestrator:**
```bash
kubectl scale deployment orchestrator --replicas=3 -n apex-pentest
```

### Auto-scaling

HPA is configured for gateway service. Check status:
```bash
kubectl get hpa -n apex-pentest
```

## Security

### Rotate Secrets

1. **Generate new secrets:**
```bash
NEW_JWT_SECRET=$(openssl rand -base64 32)
```

2. **Update secret:**
```bash
kubectl create secret generic apex-secrets \
  --from-literal=jwt-secret=$NEW_JWT_SECRET \
  --dry-run=client -o yaml | kubectl apply -f -
```

3. **Restart services:**
```bash
kubectl rollout restart deployment/gateway -n apex-pentest
```

### Update TLS Certificates

```bash
kubectl create secret tls apex-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  -n apex-pentest
```

## Maintenance

### Update Services

1. **Build new image:**
```bash
docker build -t apex-gateway:v2.0 services/gateway
docker push apex-gateway:v2.0
```

2. **Update deployment:**
```bash
kubectl set image deployment/gateway gateway=apex-gateway:v2.0 -n apex-pentest
```

3. **Monitor rollout:**
```bash
kubectl rollout status deployment/gateway -n apex-pentest
```

### Database Migrations

```bash
kubectl exec -it deployment/orchestrator -n apex-pentest -- python -m alembic upgrade head
```

## Performance Tuning

### Database Optimization

**Check slow queries:**
```sql
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Add indexes:**
```sql
CREATE INDEX idx_findings_project_severity ON findings(project_id, severity);
```

### Redis Optimization

**Check memory usage:**
```bash
kubectl exec deployment/redis -n apex-pentest -- redis-cli INFO memory
```

**Clear cache if needed:**
```bash
kubectl exec deployment/redis -n apex-pentest -- redis-cli FLUSHDB
```

## Disaster Recovery

### Complete System Restore

1. Restore database from backup
2. Restore MinIO data
3. Redeploy all services
4. Verify functionality

### Rollback Deployment

```bash
kubectl rollout undo deployment/gateway -n apex-pentest
kubectl rollout undo deployment/orchestrator -n apex-pentest
```

## Contact & Escalation

For critical issues:
1. Check this runbook
2. Review logs and metrics
3. Contact DevOps team
4. Escalate to engineering if needed
