# Registries and Repositories

## Overview

A **container registry** is like GitHub for Docker images—it's where you store, version, and share images with your team or the public. Understanding registries is essential for collaborative development and CI/CD pipelines.

In this section, you'll learn about Docker Hub, cloud registries (AWS ECR, Google Artifact Registry, Azure ACR), and how to push and pull images.

## What is a Container Registry?

A **registry** hosts Docker images. A **repository** within a registry stores versions of a specific image (identified by tags).

**Analogy:**
- **Registry** = GitHub (the platform)
- **Repository** = A single Git repo (e.g., `myapp`)
- **Tag** = A specific commit or branch (e.g., `v1.0.0`, `latest`)

**Example:**
```
docker.io/library/nginx:1.25
└──────┘ └─────┘ └───┘ └──┘
registry namespace repo  tag
```

- **Registry:** `docker.io` (Docker Hub, the default)
- **Namespace:** `library` (official images)
- **Repository:** `nginx`
- **Tag:** `1.25`

## Docker Hub: The Default Registry

**Docker Hub** ([hub.docker.com](https://hub.docker.com)) is the default public registry. It hosts millions of images, including official images for popular software.

### Official Images

Official images are maintained by Docker and the software publishers:

```bash
docker pull python:3.11
docker pull postgres:16
docker pull redis:7
docker pull nginx:1.25
```

These are heavily tested, regularly updated, and recommended for production use.

### Community Images

Anyone can publish images to Docker Hub. Search for images:

```bash
docker search elasticsearch
```

Or browse at [hub.docker.com](https://hub.docker.com).

**Best Practice:** Use official images when available. For community images, check:
- Number of pulls (popularity)
- Last updated date (maintenance)
- Dockerfile source (transparency)

### Creating a Docker Hub Account

1. Sign up at [hub.docker.com](https://hub.docker.com)
2. Log in via CLI:
   ```bash
   docker login
   # Enter username and password
   ```

Your credentials are stored in `~/.docker/config.json`.

### Pushing Images to Docker Hub

**1. Build an image:**
```bash
docker build -t myapp:latest .
```

**2. Tag the image with your Docker Hub username:**
```bash
docker tag myapp:latest YOUR_USERNAME/myapp:latest
```

**Format:** `REGISTRY/NAMESPACE/REPOSITORY:TAG`
- If registry is omitted, Docker Hub is assumed
- Namespace is your Docker Hub username

**3. Push to Docker Hub:**
```bash
docker push YOUR_USERNAME/myapp:latest
```

**Example:**
```bash
# Build
docker build -t myapp:latest .

# Tag (replace "johndoe" with your username)
docker tag myapp:latest johndoe/myapp:latest

# Push
docker push johndoe/myapp:latest

# Now anyone can pull it:
docker pull johndoe/myapp:latest
```

### Public vs. Private Repositories

**Public repositories:**
- Free on Docker Hub (unlimited)
- Anyone can pull the image

**Private repositories:**
- Require authentication to pull
- Docker Hub free tier: 1 private repo
- Paid plans: Unlimited private repos

**Create a private repository:**
1. Go to [hub.docker.com](https://hub.docker.com)
2. Create Repository → Select "Private"

## Cloud Container Registries

Cloud providers offer managed registries integrated with their ecosystems.

### AWS Elastic Container Registry (ECR)

**Benefits:**
- Integrated with AWS services (ECS, EKS, Lambda)
- IAM-based access control
- Encryption at rest and in transit
- Lifecycle policies (auto-delete old images)

**Pricing:** Pay per GB stored and GB transferred

**Usage:**

**1. Create a repository:**
```bash
aws ecr create-repository --repository-name myapp
```

**2. Authenticate Docker to ECR:**
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com
```

**3. Tag and push:**
```bash
docker tag myapp:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:latest
```

**Best Practice:** Use ECR if you're deploying on AWS (ECS, EKS, Fargate). IAM integration simplifies access management.

### Google Artifact Registry (GCR successor)

**Benefits:**
- Supports Docker images, Maven, npm, Python packages
- Integrated with Google Cloud services (Cloud Run, GKE)
- IAM-based permissions
- Vulnerability scanning

**Pricing:** Pay per GB stored

**Usage:**

**1. Create a repository:**
```bash
gcloud artifacts repositories create myapp \
  --repository-format=docker \
  --location=us-central1
```

**2. Authenticate Docker:**
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

**3. Tag and push:**
```bash
docker tag myapp:latest us-central1-docker.pkg.dev/PROJECT_ID/myapp/myapp:latest
docker push us-central1-docker.pkg.dev/PROJECT_ID/myapp/myapp:latest
```

**Note:** Google deprecated the older `gcr.io` registry in favor of Artifact Registry.

### Azure Container Registry (ACR)

**Benefits:**
- Integrated with Azure services (AKS, App Service)
- Geo-replication for global deployments
- Azure AD authentication
- Content trust (image signing)

**Pricing:** Multiple tiers (Basic, Standard, Premium) based on storage and features

**Usage:**

**1. Create a registry:**
```bash
az acr create --resource-group myResourceGroup --name myregistry --sku Basic
```

**2. Authenticate Docker:**
```bash
az acr login --name myregistry
```

**3. Tag and push:**
```bash
docker tag myapp:latest myregistry.azurecr.io/myapp:latest
docker push myregistry.azurecr.io/myapp:latest
```

### Comparison Table

| Registry | Best For | Authentication | Integration | Cost |
|----------|----------|----------------|-------------|------|
| **Docker Hub** | Public images, small teams | Username/password, tokens | CI/CD tools (GitHub Actions, CircleCI) | Free (public), paid (private) |
| **AWS ECR** | AWS deployments | IAM roles, access keys | ECS, EKS, Lambda | Pay per GB stored + transferred |
| **Google Artifact Registry** | GCP deployments | Service accounts, gcloud | Cloud Run, GKE, Cloud Build | Pay per GB stored |
| **Azure ACR** | Azure deployments | Azure AD, service principals | AKS, App Service, Azure Pipelines | Tiered pricing (Basic/Standard/Premium) |

## Image Tagging Strategies

Tags identify specific versions of an image. Common strategies:

### 1. `latest` Tag

The default tag if none is specified:

```bash
docker build -t myapp .          # Implicitly tags as myapp:latest
docker push myapp:latest
```

**Problem:** `latest` is a moving target. It doesn't automatically update on client machines—it just refers to the most recently pushed image.

**Best Practice:** Avoid `latest` in production. Pin specific versions.

### 2. Semantic Versioning

Use semver (major.minor.patch):

```bash
docker build -t myapp:1.2.3 .
docker push myapp:1.2.3

# Also push as latest
docker tag myapp:1.2.3 myapp:latest
docker push myapp:latest
```

**Benefits:**
- Clear versioning
- Rollback by pulling an older version
- Compatible with automated release tools

**Example tags:**
- `myapp:1.0.0` - Specific version
- `myapp:1.0` - Minor version family
- `myapp:1` - Major version family
- `myapp:latest` - Most recent

### 3. Git Commit SHA

Tag images with Git commit hashes for traceability:

```bash
COMMIT_SHA=$(git rev-parse --short HEAD)
docker build -t myapp:$COMMIT_SHA .
docker push myapp:$COMMIT_SHA
```

**Benefits:**
- Precise traceability to source code
- Useful in CI/CD (every commit builds a unique image)

**Example:**
```bash
docker pull myapp:a3f2c1b
# Corresponds to Git commit a3f2c1b
```

### 4. Environment-Specific Tags

Tag for specific environments:

```bash
docker tag myapp:1.2.3 myapp:production
docker tag myapp:1.2.3 myapp:staging
```

**Use case:** Deploy different versions to staging and production simultaneously.

### 5. Combined Strategy (Recommended)

Use multiple tags for flexibility:

```bash
# Build with commit SHA
COMMIT_SHA=$(git rev-parse --short HEAD)
docker build -t myapp:$COMMIT_SHA .

# Add semver tag
docker tag myapp:$COMMIT_SHA myapp:1.2.3

# Add latest tag
docker tag myapp:$COMMIT_SHA myapp:latest

# Push all tags
docker push myapp:$COMMIT_SHA
docker push myapp:1.2.3
docker push myapp:latest
```

**At Scale:** In CI/CD, automate tagging with semver + SHA + environment labels.

## Pulling Images

Pull images from a registry:

```bash
# Pull from Docker Hub (default)
docker pull nginx:1.25

# Pull from a specific registry
docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:latest

# Pull a private image (requires authentication)
docker login
docker pull johndoe/private-app:latest
```

**Advanced:** Pull multi-architecture images. Docker automatically selects the correct variant (x86_64, ARM64) for your platform.

## Multi-Architecture Images

Modern applications run on diverse hardware (x86_64 servers, ARM64 cloud instances, Apple Silicon Macs). **Multi-architecture images** contain variants for different platforms.

**Build multi-arch images with Buildx:**

```bash
# Create a builder (one-time setup)
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t johndoe/myapp:latest \
  --push .
```

Docker pushes a **manifest list** to the registry. When users pull `johndoe/myapp:latest`, Docker selects the appropriate architecture.

**Why it matters:**
- **Cloud:** AWS Graviton (ARM64) instances are cheaper and efficient
- **Development:** Apple Silicon Macs use ARM64
- **Production:** Most servers are x86_64

**Best Practice:** Always build for `linux/amd64` at minimum. Add `linux/arm64` for cloud cost optimization.

## Private Registry Authentication

For private registries, Docker needs credentials.

**Manual login:**
```bash
docker login registry.example.com
# Enter username and password
```

**Token-based authentication (Docker Hub):**
1. Create a personal access token at [hub.docker.com/settings/security](https://hub.docker.com/settings/security)
2. Use token as password:
   ```bash
   docker login -u YOUR_USERNAME --password-stdin <<< YOUR_TOKEN
   ```

**CI/CD authentication:**
- **GitHub Actions:** Use `docker/login-action` with secrets
- **AWS ECS/EKS:** IAM roles automatically authenticate with ECR
- **Kubernetes:** Use `imagePullSecrets` for private registries

**Example GitHub Actions workflow:**
```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v2
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_TOKEN }}

- name: Build and push
  run: |
    docker build -t johndoe/myapp:${{ github.sha }} .
    docker push johndoe/myapp:${{ github.sha }}
```

## Image Lifecycle Management

Registries accumulate images over time, consuming storage and costing money. Implement lifecycle policies:

**Docker Hub:** Manual deletion via web UI or API

**AWS ECR:** Lifecycle policies to auto-delete old images:
```json
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
```

**Google Artifact Registry:** Retention policies and cleanup scripts

**Best Practice:** Keep the last N versions, delete untagged images, and automate cleanup in CI/CD.

## At Scale: Registry Best Practices

**1. Security:**
- Scan images for vulnerabilities (Trivy, Snyk, cloud-native scanners)
- Use signed images (Docker Content Trust, Sigstore)
- Restrict access with IAM policies

**2. Performance:**
- Use regional registries (e.g., ECR in `us-east-1` for ECS clusters in `us-east-1`)
- Enable caching layers in CI/CD (Docker layer caching, BuildKit)

**3. Cost Optimization:**
- Delete unused images regularly
- Use lifecycle policies
- Compress layers (multi-stage builds, slim base images)

**4. Monitoring:**
- Track image pull counts
- Alert on failed image pushes
- Monitor storage usage

## Summary

Container registries store and share Docker images. Docker Hub is the default public registry, while cloud providers offer ECR (AWS), Artifact Registry (Google), and ACR (Azure) with deep cloud integration. Tag images with semantic versions or Git SHAs for traceability, and use multi-architecture builds for diverse hardware. Implement lifecycle policies to manage storage costs.

**Key Takeaways:**
- **Registries** store images; **repositories** store versions of an image
- **Docker Hub** is the default, great for public images
- **Cloud registries** (ECR, Artifact Registry, ACR) integrate with cloud services
- **Tag images** with semver, Git SHAs, or environment labels
- **Multi-arch images** support x86_64 and ARM64 with a single tag
- **Lifecycle policies** prevent registries from growing unbounded
- Use **private registries** for proprietary code

---

**Previous:** [Distributed System Demo](../03-docker-compose/02-distributed-system-demo.md) | **Next:** [CI/CD and Cloud Deployment](02-cicd-and-cloud-deployment.md)
