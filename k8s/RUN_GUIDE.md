# Запуск проекта Sweater в Rancher Desktop (Kubernetes)

## Структура проекта

```
project/
├── app.py                  # Backend (Flask + PostgreSQL)
├── Dockerfile.backend      # Dockerfile для backend
├── Dockerfile.frontend     # Dockerfile для frontend (nginx)
├── nginx.conf              # Конфигурация nginx
├── docker-compose.yml      # Docker Compose (не используется в K8s)
├── requirements.txt        # Python зависимости
└── k8s/                    # Kubernetes манифесты
    ├── namespace.yaml      # Namespace sweater
    ├── configmap.yaml      # ConfigMap (несекретные переменные)
    ├── secret.yaml         # Secret (пароль PostgreSQL)
    ├── pvc.yaml            # PersistentVolumeClaim для PostgreSQL
    ├── postgres-deployment.yaml
    ├── postgres-service.yaml
    ├── backend-deployment.yaml
    ├── backend-service.yaml
    ├── frontend-deployment.yaml
    ├── frontend-service.yaml
    └── ingress.yaml        # Ingress (маршрутизация через Traefik)
```

---

## Шаг 1 — Очистка (если запускалось раньше)

```cmd
kubectl delete namespace sweater
```

> Если раньше использовался namespace `filestorage` — удали и его: `kubectl delete namespace filestorage`.

---

## Шаг 2 — Добавить hosts

Открой `C:\Windows\System32\drivers\etc\hosts` от имени администратора и добавь строку:

```
127.0.0.1 sweater.local
```

---

## Шаг 3 — Собрать образы

Из корня папки `project`:

```cmd
docker build -t sweater-backend:latest -f Dockerfile.backend .
docker build -t sweater-frontend:latest -f Dockerfile.frontend .
```

> Манифесты используют `imagePullPolicy: Never` — образы берутся из локального движка Rancher Desktop,
> а не из внешнего реестра, поэтому теги должны точно совпадать: `sweater-backend:latest`, `sweater-frontend:latest`.

---

## Шаг 4 — Применить манифесты

```cmd
kubectl apply -f k8s/
```

Если ошибки `namespace not found` — запусти ещё раз (namespace создаётся первым).

---

## Шаг 5 — Проверить статус

```cmd
kubectl get all -n sweater
```

Все pods должны быть `Running`.

---

## Шаг 6 — Открыть приложение

```
http://sweater.local
```

Или, если Ingress не настроен:

```
http://localhost:30080
```

---

## Описание манифестов

| Файл | Что делает |
|------|------------|
| `namespace.yaml` | Создаёт namespace `sweater` для изоляции ресурсов приложения. |
| `configmap.yaml` | `sweater-config` — несекретные переменные (`POSTGRES_DB`, `POSTGRES_USER`, `DB_HOST`, `DB_PORT`, `FLASK_ENV`). Подключается через `configMapKeyRef`. |
| `secret.yaml` | `sweater-secret` — пароль PostgreSQL (`POSTGRES_PASSWORD`). Подключается через `secretKeyRef`. |
| `pvc.yaml` | `postgres-data` — постоянный том 1Gi для данных PostgreSQL (`ReadWriteOnce`). |
| `postgres-deployment.yaml` | 1 pod PostgreSQL. `strategy: Recreate` (нельзя два экземпляра на одном томе). Пароль — из Secret. `pg_isready` в probes. |
| `postgres-service.yaml` | ClusterIP для доступа backend к БД по имени `postgres:5432`. |
| `backend-deployment.yaml` | 1 pod Flask. `initContainer` ждёт PostgreSQL (`nc -z postgres 5432`). Переменные БД — из ConfigMap + Secret (полный URL собирает `app.py`). `imagePullPolicy: Never`. |
| `backend-service.yaml` | ClusterIP для доступа к backend из frontend и ingress. |
| `frontend-deployment.yaml` | 1 pod nginx со статикой. Лимиты 300m CPU / 256Mi RAM. `imagePullPolicy: Never`. |
| `frontend-service.yaml` | NodePort `30080` для доступа к frontend извне кластера. |
| `ingress.yaml` | `sweater-ingress` (Traefik): `sweater.local/api` и `/health` → backend:5000, `/` → frontend:80. |

> **Безопасность:** пароль БД хранится в объекте `Secret` (`sweater-secret`). В этом учебном проекте Secret
> закоммичен с примерным паролем. Для реального кластера секреты не коммитят в git — используют
> Sealed Secrets / External Secrets / Vault.

---

## Команды для управления

| Команда | Описание |
|---------|----------|
| `kubectl get all -n sweater` | Показать все ресурсы |
| `kubectl get pods -n sweater` | Показать pods |
| `kubectl get ingress -n sweater` | Показать ingress |
| `kubectl logs -f deployment/backend -n sweater` | Логи backend |
| `kubectl rollout restart deployment/backend -n sweater` | Перезапустить backend |
| `kubectl delete -f k8s/` | Удалить всё |

---

## Устранение проблем

**ImagePullBackOff / ErrImageNeverPull** — образ не найден локально. Собери образы с тегами
`sweater-backend:latest` и `sweater-frontend:latest` (Шаг 3).

**Connection refused на http://sweater.local** — проверь hosts-файл и ingress:
```cmd
kubectl get ingress -n sweater
```

**Backend в CrashLoopBackOff / не может подключиться к БД** — посмотри логи:
```cmd
kubectl logs -f deployment/backend -n sweater
```
Если БД создавалась со старым паролем (старый PVC) — удали namespace и PVC и подними заново:
```cmd
kubectl delete namespace sweater
kubectl apply -f k8s/
```

**Дефолтная страница nginx** — пересобери frontend и перезапусти pod:
```cmd
docker build -t sweater-frontend:latest -f Dockerfile.frontend .
kubectl delete pod -l app=frontend -n sweater
```
