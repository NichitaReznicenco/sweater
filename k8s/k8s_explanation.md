# Объяснение объектов Kubernetes

Все объекты разворачиваются в namespace `sweater` командой `kubectl apply -f k8s/`.

---

## 1. Namespace (namespace.yaml)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sweater
  labels:
    app.kubernetes.io/part-of: sweater
```

**Namespace** — виртуальный кластер внутри физического. Изолирует ресурсы проекта. Все объекты
(Deployment, Service, ConfigMap, Secret) создаются в namespace `sweater`.

---

## 2. ConfigMap и Secret (configmap.yaml, secret.yaml)

**ConfigMap** (`sweater-config`) хранит несекретные переменные: `POSTGRES_DB`, `POSTGRES_USER`,
`DB_HOST`, `DB_PORT`, `FLASK_ENV`. Подключается к подам через `configMapKeyRef`.

**Secret** (`sweater-secret`) хранит пароль PostgreSQL (`POSTGRES_PASSWORD`). Подключается через
`secretKeyRef`. В реальном кластере секреты не коммитят в git (используют Sealed Secrets / Vault).

---

## 3. PersistentVolumeClaim (pvc.yaml)

```yaml
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
```

**PVC** (`postgres-data`) запрашивает постоянный том на 1Gi. Данные PostgreSQL не теряются при
перезапуске пода. `ReadWriteOnce` — том монтируется к одному поду.

---

## 4. Deployment PostgreSQL (postgres-deployment.yaml)

**Deployment** описывает, как развернуть приложение (сколько реплик, какой образ, переменные).

```yaml
spec:
  replicas: 1
  strategy:
    type: Recreate
```
- **replicas: 1** — для БД одна реплика (масштабирование не нужно).
- **strategy: Recreate** — старый pod останавливается до создания нового, потому что один том PVC
  нельзя подключить к двум подам одновременно.

Пароль берётся из Secret:
```yaml
env:
  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: sweater-secret
        key: POSTGRES_PASSWORD
```

Том PVC монтируется в `/var/lib/postgresql/data`. `readinessProbe`/`livenessProbe` проверяют БД через
`pg_isready`.

---

## 5. Service PostgreSQL (postgres-service.yaml)

**Service** — стабильный сетевой endpoint для подов. Тип по умолчанию — **ClusterIP** (доступен только
внутри кластера). Backend обращается к БД по имени `postgres:5432`.

---

## 6. Deployment Backend (backend-deployment.yaml)

```yaml
spec:
  replicas: 1
```

- **initContainer `wait-for-postgres`** — ждёт доступности БД (`nc -z postgres 5432`) до старта Flask.
- Переменные подключения (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DB_HOST`, `DB_PORT`)
  берутся из ConfigMap и Secret; полный URL собирает `app.py`.
- **imagePullPolicy: Never** — используется локальный образ `sweater-backend:latest`.

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 5000
readinessProbe:
  httpGet:
    path: /
    port: 5000
```
**livenessProbe** перезапускает зависший контейнер; **readinessProbe** убирает не готовый pod из
балансировки.

---

## 7. Service Backend (backend-service.yaml)

ClusterIP. Другие поды обращаются к backend по имени `backend` (или
`backend.sweater.svc.cluster.local`) на порту 5000.

---

## 8. Deployment Frontend (frontend-deployment.yaml)

1 реплика nginx со статикой. Образ `sweater-frontend:latest` (`imagePullPolicy: Never`).
Ресурсы ограничены: 300m CPU / 256Mi RAM.

---

## 9. Service Frontend (frontend-service.yaml)

```yaml
type: NodePort
ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
```

**NodePort** открывает порт `30080` на нодах кластера — доступ извне по `http://localhost:30080`.
Альтернатива для облаков — LoadBalancer (GKE, EKS).

---

## 10. Ingress (ingress.yaml)

`sweater-ingress` (Traefik, встроен в Rancher Desktop) маршрутизирует по URL:
- `sweater.local/api/*` → backend:5000
- `sweater.local/health/*` → backend:5000
- `sweater.local/*` → frontend:80

---

## СХЕМА ВЗАИМОДЕЙСТВИЯ

```
┌─────────────────────────────────────────────────────────┐
│  Namespace: sweater                                       │
│                                                           │
│  Ingress (sweater.local) ──/api,/health──► backend:5000   │
│         │                                                 │
│         └──/──► frontend:80 (NodePort 30080)              │
│                                                           │
│  ┌─────────┐      ┌──────────┐      ┌──────────┐          │
│  │Frontend │      │ Backend  │─────►│ Postgres │          │
│  │ Service │      │ Service  │      │ Service  │          │
│  └────┬────┘      └────┬─────┘      └────┬─────┘          │
│  ┌────┴────┐      ┌────┴─────┐      ┌────┴─────┐          │
│  │ FE Pod  │      │ BE Pod   │      │ PG Pod   │──► PVC    │
│  │ (nginx) │      │ (flask)  │      │(postgres)│  1Gi      │
│  └─────────┘      └──────────┘      └──────────┘          │
└─────────────────────────────────────────────────────────┘
```

---

## КОМАНДЫ kubectl

```bash
# Применить все манифесты
kubectl apply -f k8s/

# Посмотреть статус
kubectl get all -n sweater

# Удалить всё
kubectl delete -f k8s/

# Логи backend
kubectl logs -n sweater -l app=backend

# Описание объекта
kubectl describe deployment backend -n sweater
```
