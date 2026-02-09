# CI/CD and Cloud Deployment

## Overview

Docker's "build once, run anywhere" promise makes it ideal for CI/CD pipelines. Build an image in your pipeline, push it to a registry, and deploy it to the cloud—all automated. In this section, you'll learn how Docker fits into modern deployment workflows, common CI/CD tools, and cloud deployment patterns.

## The CI/CD Journey with Docker

**Traditional deployment:**
1. Developer commits code
2. CI system runs tests
3. Ops team manually deploys to servers
4. Environment differences cause "works on my machine" issues

**Docker-based deployment:**
1. Developer commits code
2. CI builds Docker image and runs tests inside containers
3. CI pushes image to registry
4. CD automatically deploys container to production
5. Same image runs everywhere (dev, staging, prod)

**Benefits:**
- **Reproducibility:** Same image from laptop to production
- **Fast rollback:** Redeploy a previous image version
- **Isolation:** Dependencies packaged with the app
- **Scalability:** Containers start in seconds

## Typical CI/CD Workflow

```mermaid
graph LR
    Dev[Developer] -->|git push| Repo[Git Repository]
    Repo -->|webhook| CI[CI Pipeline]
    CI -->|build| Image[Docker Image]
    CI -->|test| Image
    Image -->|push| Registry[Container Registry]
    Registry -->|pull| CD[CD System]
    CD -->|deploy| Cloud[Cloud Platform]
    Cloud -->|ECS/GKE/AKS| Running[Running Containers]
```

**Stages:**

1. **Code Commit:** Developer pushes to Git (GitHub, GitLab, Bitbucket)
2. **Build:** CI system (GitHub Actions, GitLab CI, Jenkins) builds Docker image
3. **Test:** Run unit tests, integration tests in containers
4. **Push:** Push image to registry (Docker Hub, ECR, Artifact Registry)
5. **Deploy:** CD system deploys image to cloud (ECS, GKE, Cloud Run)
6. **Monitor:** Observe logs, metrics, errors

**Why test in containers?**
- **Consistency:** Tests run in the same environment as production
- **Isolation:** Test dependencies packaged with the app
- **Reproducibility:** Same results on any machine or CI system
- **Fast feedback:** Catch issues before pushing to registry

**Testing strategies:**
- **Unit tests:** Test individual functions/classes inside container
- **Integration tests:** Test API endpoints, database connections with test database containers
- **Security scanning:** Scan images for vulnerabilities (Trivy, Snyk, Clair)
- **Smoke tests:** Deploy to staging, run basic health checks before production

## Example: GitHub Actions Pipeline

**Scenario:** Build and deploy a FastAPI app to AWS ECS on every push to `main`.

**.github/workflows/deploy.yml:**
```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: myapp
  ECS_SERVICE: myapp-service
  ECS_CLUSTER: myapp-cluster

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Log in to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build and tag image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Run tests
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          # Run unit tests inside the container
          docker run --rm $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG pytest tests/unit -v
          
          # Run integration tests with test database
          docker run --rm \
            -e DATABASE_URL=postgresql://test:test@testdb:5432/testdb \
            --network test-network \
            $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
            pytest tests/integration -v

      - name: Push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --force-new-deployment

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services $ECS_SERVICE
```

**How it works:**
1. **Checkout code:** Pull the latest code from Git
2. **AWS credentials:** Authenticate with AWS using GitHub Secrets
3. **Log in to ECR:** Get Docker credentials for AWS ECR
4. **Build and tag:** Build image tagged with Git SHA and `latest`
5. **Run tests:** Execute unit and integration tests inside the container
6. **Push:** Push images to ECR (only if tests pass)
7. **Deploy to ECS:** Trigger ECS service update (pulls new image)
8. **Wait:** Wait for ECS to finish deploying (health checks pass)

**Best Practice:** Tag images with Git SHA for traceability. If a deployment fails, you know exactly which commit caused it.

## Common CI/CD Tools

### GitHub Actions

**Pros:**
- Native integration with GitHub repos
- Free for public repos, generous free tier for private
- Large marketplace of actions (pre-built steps)

**Use case:** Most projects on GitHub

**Docker-specific actions:**
- `docker/login-action` - Authenticate to registries
- `docker/build-push-action` - Build and push images
- `docker/setup-buildx-action` - Enable BuildKit features

### GitLab CI/CD

**Pros:**
- Integrated with GitLab (code, CI, registry all in one platform)
- Built-in container registry
- Kubernetes integration

**Example `.gitlab-ci.yml`:**
```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

test:
  stage: test
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker pull $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker run --rm $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA pytest tests/ -v

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Jenkins

**Pros:**
- Highly customizable (plugins for everything)
- Self-hosted (full control over infrastructure)
- Mature ecosystem

**Cons:**
- Requires setup and maintenance (unlike cloud CI services)

**Use case:** Large enterprises with existing Jenkins infrastructure

### CircleCI / Travis CI / Azure DevOps

Other popular CI platforms with Docker support. Principles are the same: build image, push to registry, trigger deployment.

## Cloud Deployment Patterns

### AWS: Elastic Container Service (ECS) / Fargate

**ECS:** Managed container orchestration on AWS. You define tasks (containers) and services (long-running tasks).

**Fargate:** Serverless ECS—AWS manages the infrastructure. You just define containers and resource limits.

**Workflow:**
1. Push image to ECR
2. Create ECS task definition (JSON specifying image, CPU, memory, ports)
3. Create ECS service (runs N tasks, load balancer integration)
4. Deploy: Update service with new task definition

**Example task definition:**
```json
{
  "family": "myapp",
  "containerDefinitions": [
    {
      "name": "myapp",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:latest",
      "cpu": 256,
      "memory": 512,
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."}
      ]
    }
  ]
}
```

**Deploy:**
```bash
aws ecs update-service --cluster mycluster --service myapp --force-new-deployment
```

**Best for:** AWS-centric infrastructure, need tight integration with other AWS services (RDS, S3, Lambda).

### Google Cloud: Cloud Run

**Cloud Run:** Serverless container platform. Automatically scales to zero (no cost when idle) and scales up based on traffic.

**Workflow:**
1. Push image to Artifact Registry
2. Deploy with `gcloud run deploy`
3. Cloud Run handles everything (HTTPS, scaling, load balancing)

**Deploy:**
```bash
gcloud run deploy myapp \
  --image us-central1-docker.pkg.dev/PROJECT_ID/myapp/myapp:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Benefits:**
- **Serverless:** Pay only for requests (scales to zero)
- **Simple:** No cluster management
- **Fast:** Containers start in seconds

**Best for:** APIs, web services with variable traffic.

### Google Cloud: Kubernetes Engine (GKE)

**GKE:** Managed Kubernetes on Google Cloud.

**Workflow:**
1. Push image to Artifact Registry
2. Create Kubernetes deployment YAML
3. Apply with `kubectl apply -f deployment.yml`

**Example deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: us-central1-docker.pkg.dev/PROJECT_ID/myapp/myapp:latest
        ports:
        - containerPort: 8000
```

**Best for:** Complex microservices, need advanced orchestration (auto-scaling, rolling updates, service mesh).

### Azure: Container Instances / App Service / AKS

**Azure Container Instances (ACI):**
- Serverless containers (similar to Cloud Run)
- Fast startup, pay per second
- Good for batch jobs, burst workloads

**Azure App Service:**
- PaaS with container support
- Integrated with Azure DevOps

**Azure Kubernetes Service (AKS):**
- Managed Kubernetes on Azure

**Best for:** Azure-centric shops.

## Kubernetes: The De Facto Orchestrator

For large-scale production, **Kubernetes** is the industry standard. It provides:
- **Declarative configuration:** Define desired state, Kubernetes maintains it
- **Self-healing:** Restart failed containers, replace unhealthy nodes
- **Auto-scaling:** Scale pods based on CPU/memory/custom metrics
- **Rolling updates:** Deploy new versions with zero downtime
- **Service discovery and load balancing:** Built-in DNS and load balancing

**Basic concepts:**
- **Pod:** One or more containers (smallest deployable unit)
- **Deployment:** Manages replicas of a pod (scaling, updates)
- **Service:** Stable endpoint for accessing pods (load balancer)
- **ConfigMap / Secret:** Configuration and secrets injection

**Example deployment + service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myregistry.io/myapp:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
```

**Deploy:**
```bash
kubectl apply -f deployment.yml
kubectl get pods
kubectl get services
```

**Advanced Note:** Kubernetes is complex. For simpler needs, managed services (Cloud Run, ECS Fargate) may be sufficient. Use Kubernetes when you need advanced orchestration, multi-cloud portability, or have complex microservices.

## Infrastructure as Code (IaC)

Define cloud infrastructure in code (Terraform, Pulumi, CloudFormation) for reproducibility.

**Example: Terraform for ECS**
```hcl
resource "aws_ecs_cluster" "main" {
  name = "myapp-cluster"
}

resource "aws_ecs_task_definition" "myapp" {
  family                = "myapp"
  container_definitions = file("task-definition.json")
  requires_compatibilities = ["FARGATE"]
  network_mode          = "awsvpc"
  cpu                   = "256"
  memory                = "512"
}

resource "aws_ecs_service" "myapp" {
  name            = "myapp-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.myapp.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  # ... network config, load balancer ...
}
```

**Benefits:**
- **Version control:** Infrastructure changes tracked in Git
- **Reproducibility:** Spin up identical environments (staging, prod)
- **Collaboration:** Infrastructure code reviewed like application code

## Secrets Management

Never hardcode secrets in Dockerfiles or images.

**Options:**

**1. Environment variables (passed at runtime):**
```bash
docker run -e DATABASE_PASSWORD=secret myapp
```

**2. Secrets managers:**
- **AWS Secrets Manager / Parameter Store**
- **Google Secret Manager**
- **Azure Key Vault**
- **HashiCorp Vault**

**Example: AWS ECS with Secrets Manager**
```json
{
  "containerDefinitions": [
    {
      "name": "myapp",
      "secrets": [
        {
          "name": "DATABASE_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-password"
        }
      ]
    }
  ]
}
```

**3. Kubernetes Secrets:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  password: cGFzc3dvcmQxMjM=  # base64 encoded
```

Reference in deployment:
```yaml
containers:
- name: myapp
  env:
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: password
```

**Best Practice:** Use secrets managers in production. Rotate secrets regularly. Audit access to secrets.

## Monitoring and Observability

Once containers are running in production, monitor them:

**Logs:**
- **CloudWatch Logs (AWS)**, **Stackdriver Logging (GCP)**, **Azure Monitor**
- **ELK Stack (Elasticsearch, Logstash, Kibana)**
- **Grafana Loki**, **Splunk**

**Metrics:**
- **Prometheus + Grafana** (industry standard for Kubernetes)
- **CloudWatch Metrics (AWS)**, **Cloud Monitoring (GCP)**, **Azure Monitor**

**Tracing:**
- **Jaeger**, **Zipkin**, **AWS X-Ray**, **Google Cloud Trace**

**Application Performance Monitoring (APM):**
- **Datadog**, **New Relic**, **Dynatrace**

**Best Practice:** Implement the "three pillars of observability":
1. **Logs:** What happened (events, errors)
2. **Metrics:** How much/how often (CPU, memory, request rate)
3. **Traces:** End-to-end request flow across services

## At Scale: Production Best Practices

**1. Health Checks:**
- Define health endpoints (`/health`, `/readiness`)
- Configure health checks in ECS, Kubernetes, load balancers
- Prevents routing traffic to unhealthy containers

**2. Resource Limits:**
- Set CPU and memory limits in task definitions / Kubernetes pods
- Prevents one container from starving others

**3. Rolling Updates:**
- Deploy new versions gradually (e.g., 1 pod at a time)
- Kubernetes handles this automatically with `RollingUpdate` strategy

**4. Blue-Green Deployments:**
- Run two environments (blue = current, green = new)
- Switch traffic to green after validation
- Instant rollback if issues arise

**5. Canary Deployments:**
- Route small percentage of traffic to new version
- Gradually increase if metrics are healthy
- Rollback if error rates spike

**6. Immutable Infrastructure:**
- Never modify running containers—deploy new versions
- Ensures consistency and simplifies rollback

**7. Least Privilege:**
- Run containers as non-root users
- Use read-only filesystems where possible
- Apply security policies (Pod Security Policies in Kubernetes)

## Summary

Docker enables modern CI/CD workflows: build images in CI, push to registries, deploy to cloud platforms. Common deployment targets include AWS ECS/Fargate, Google Cloud Run/GKE, and Azure ACI/AKS. Kubernetes is the de facto standard for large-scale orchestration. Use secrets managers for sensitive data, monitor logs/metrics/traces, and implement health checks and rolling updates for reliability.

**Key Takeaways:**
- **CI/CD workflow:** Code → Build image → Test → Push to registry → Deploy
- **GitHub Actions, GitLab CI, Jenkins** are popular CI tools
- **AWS ECS, Google Cloud Run, Kubernetes** are common deployment targets
- **Tag images with Git SHA** for traceability
- **Use secrets managers** for passwords, API keys
- **Monitor logs, metrics, traces** in production
- **Kubernetes** provides advanced orchestration for complex systems

---

**Previous:** [Registries and Repositories](01-registries-and-repositories.md) | **Next:** [VSCode Dev Containers](03-vscode-dev-containers.md)
