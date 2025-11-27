# Deployment Guide

This guide covers production deployment strategies for Spermophilus OCR bot, including Docker, cloud platforms, and monitoring.

## 🐳 Docker Deployment

### Quick Start with Docker Compose

```bash
# Clone and setup
git clone <repository-url>
cd Spermophilus

# Configure environment
cp .env.example .env
# Edit .env with your production settings

# Deploy
docker-compose up -d
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  ocr-bot:
    build: .
    container_name: spermophilus-ocr
    restart: unless-stopped
    network_mode: host
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - ALLOWED_USER_IDS=${ALLOWED_USER_IDS}
      - LM_STUDIO_URL=${LM_STUDIO_URL}
      - WORKER_NAME=${WORKER_NAME:-worker_1}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:1234/v1/models"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    container_name: spermophilus-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

### Multi-Stage Dockerfile

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim-bookworm as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Production stage
FROM python:3.11-slim-bookworm

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy UV and dependencies
COPY --from=builder /bin/uv /bin/uv
COPY --from=builder /app/.venv /app/.venv

# Create app user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1

# Copy application code
COPY --chown=appuser:appuser . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:1234/v1/models || exit 1

# Run
CMD ["python", "-m", "src.main"]
```

## ☁️ Cloud Deployment

### AWS Deployment

#### EC2 Instance Setup

```bash
# 1. Launch EC2 instance (Ubuntu 22.04)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# 4. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. Clone and deploy
git clone <repository-url>
cd Spermophilus
cp .env.example .env
# Edit .env with production values
docker-compose -f docker-compose.prod.yml up -d
```

#### ECS Deployment

```json
// ecs-task-definition.json
{
  "family": "spermophilus-ocr",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "ocr-bot",
      "image": "your-account.dkr.ecr.region.amazonaws.com/spermophilus:latest",
      "portMappings": [],
      "environment": [
        {
          "name": "TELEGRAM_BOT_TOKEN",
          "value": "your-token"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/spermophilus",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

#### Cloud Run Deployment

```dockerfile
# Dockerfile.cloud-run
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run expects port 8080
EXPOSE 8080

# Use Cloud Run's web server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "src.web_api:app"]
```

```bash
# Deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT-ID/spermophilus
gcloud run deploy spermophilus-ocr \
  --image gcr.io/PROJECT-ID/spermophilus \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "TELEGRAM_BOT_TOKEN=$TOKEN,ALLOWED_USER_IDS=$USERS"
```

### Azure Container Instances

```yaml
# azure-container.yaml
apiVersion: 2019-12-01
location: eastus
name: spermophilus-ocr
properties:
  containers:
  - name: ocr-bot
    properties:
      image: your-registry.azurecr.io/spermophilus:latest
      resources:
        requests:
          cpu: 1.0
          memoryInGb: 2.0
      environmentVariables:
      - name: TELEGRAM_BOT_TOKEN
        value: "your-token"
      - name: ALLOWED_USER_IDS
        value: "123,456"
  osType: Linux
  restartPolicy: Always
tags: null
type: Microsoft.ContainerInstance/containerGroups
```

## 🔧 Production Configuration

### Environment Variables

```bash
# .env.production
TELEGRAM_BOT_TOKEN=your_production_token
ALLOWED_USER_IDS=123,456,789
LM_STUDIO_URL=http://lm-server:1234/v1
WORKER_NAME=prod_worker_1
LOG_LEVEL=INFO

# Production-specific
DATABASE_URL=sqlite:///data/ocr.db
REDIS_URL=redis://redis:6379/0
MAX_FILE_SIZE_MB=10
MAX_CONCURRENT_JOBS=3
HEALTH_CHECK_INTERVAL=30
```

### Nginx Reverse Proxy

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream ocr_bot {
        server ocr-bot:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://ocr_bot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### Docker Compose with Nginx

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: spermophilus-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - ocr-bot

  ocr-bot:
    build: .
    container_name: spermophilus-ocr
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - ALLOWED_USER_IDS=${ALLOWED_USER_IDS}
      - LM_STUDIO_URL=${LM_STUDIO_URL}
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    container_name: spermophilus-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## 📊 Monitoring and Logging

### Prometheus Monitoring

```python
# src/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
jobs_processed = Counter('ocr_jobs_processed_total', 'Total OCR jobs processed')
job_duration = Histogram('ocr_job_duration_seconds', 'OCR job processing time')
active_jobs = Gauge('ocr_active_jobs', 'Number of active OCR jobs')
api_errors = Counter('ocr_api_errors_total', 'Total API errors')

def start_metrics_server(port=8000):
    """Start Prometheus metrics server."""
    start_http_server(port)
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Spermophilus OCR Bot",
    "panels": [
      {
        "title": "Jobs Processed",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(ocr_jobs_processed_total[5m])",
            "legendFormat": "Jobs/sec"
          }
        ]
      },
      {
        "title": "Processing Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ocr_job_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack Integration

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

## 🔒 Security Hardening

### SSL/TLS Configuration

```bash
# Generate SSL certificates
sudo certbot --nginx -d your-domain.com

# Or use self-signed for development
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private.key -out ssl/certificate.crt
```

### Firewall Configuration

```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Container Security

```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  ocr-bot:
    build: .
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    volumes:
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
```

## 🚀 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check
      - run: uv run pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t spermophilus:${{ github.sha }} .
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag spermophilus:${{ github.sha }} your-registry/spermophilus:latest
          docker push your-registry/spermophilus:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          ssh user@server "cd /app && docker-compose pull && docker-compose up -d"
```

### GitLab CI/CD

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: python:3.11
  script:
    - pip install uv
    - uv sync
    - uv run ruff check
    - uv run pytest

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - ssh $DEPLOY_SERVER "cd /app && docker-compose pull && docker-compose up -d"
  only:
    - main
```

## 📈 Scaling Strategies

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  ocr-bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - WORKER_NAME=worker_${HOSTNAME}
    volumes:
      - shared_data:/app/data
    deploy:
      replicas: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    depends_on:
      - ocr-bot

volumes:
  shared_data:
```

### Load Balancer Configuration

```nginx
# nginx-lb.conf
upstream ocr_backend {
    least_conn;
    server ocr-bot_1:8000;
    server ocr-bot_2:8000;
    server ocr-bot_3:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://ocr_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 Maintenance

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Backup database
sqlite3 data/ocr.db ".backup backup/ocr_$(date +%Y%m%d_%H%M%S).db"

# Backup configuration
tar -czf backup/config_$(date +%Y%m%d_%H%M%S).tar.gz .env docker-compose*.yml

# Cleanup old backups (keep 30 days)
find backup/ -name "*.db" -mtime +30 -delete
find backup/ -name "*.tar.gz" -mtime +30 -delete
```

### Health Monitoring

```python
# src/health.py
import asyncio
import aiohttp
import structlog

logger = structlog.get_logger()

async def health_check():
    """Comprehensive health check."""
    checks = {
        "database": check_database,
        "lm_studio": check_lm_studio,
        "disk_space": check_disk_space,
        "memory": check_memory,
    }
    
    results = {}
    for name, check_func in checks.items():
        try:
            results[name] = await check_func()
        except Exception as e:
            logger.error(f"Health check failed: {name}", error=str(e))
            results[name] = {"status": "unhealthy", "error": str(e)}
    
    return results

async def check_database():
    """Check database connectivity."""
    # Implementation here
    pass

async def check_lm_studio():
    """Check LM Studio API."""
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:1234/v1/models") as resp:
            return {"status": "healthy" if resp.status == 200 else "unhealthy"}
```

### Log Rotation

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  ocr-bot:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=ocr-bot"

  logrotate:
    image: blacklabelops/logrotate
    volumes:
      - ./logs:/logs
      - ./logrotate.conf:/etc/logrotate.d/logrotate.conf
    environment:
      - LOGS_DIRECTORIES=/logs
      - LOGROTATE_COPIES=5
      - LOGROTATE_INTERVAL=daily
      - LOGROTATE_SIZE=10M
```

## 🚨 Troubleshooting Production Issues

### Common Production Problems

1. **Memory Leaks**
   ```bash
   # Monitor memory usage
   docker stats
   
   # Restart container if needed
   docker-compose restart ocr-bot
   ```

2. **Database Locks**
   ```bash
   # Check for locks
   sqlite3 data/ocr.db "PRAGMA lock_status;"
   
   # Clear locks
   docker-compose restart ocr-bot
   ```

3. **LM Studio Disconnection**
   ```bash
   # Check connectivity
   curl http://localhost:1234/v1/models
   
   # Restart LM Studio service
   ```

### Performance Tuning

```bash
# Optimize SQLite
sqlite3 data/ocr.db "PRAGMA journal_mode=WAL;"
sqlite3 data/ocr.db "PRAGMA synchronous=NORMAL;"
sqlite3 data/ocr.db "PRAGMA cache_size=10000;"
```

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring setup
- [ ] Log rotation configured
- [ ] Security hardening applied

### Post-Deployment

- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on operations

Your Spermophilus OCR bot is now production-ready! 🎉