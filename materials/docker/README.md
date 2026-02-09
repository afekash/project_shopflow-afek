# Docker

## Overview

This module provides a comprehensive introduction to Docker and containerization for data engineering workflows. You'll learn to package applications in portable containers, orchestrate multi-service systems with Docker Compose, and understand how containers fit into modern cloud-native architectures.

**Duration:** 4 hours

**Prerequisites:**
- Basic command-line familiarity (bash/terminal)
- Understanding of Python and web applications
- Docker Desktop installed on your system

## Why Docker for Data Engineers?

Data engineering involves building pipelines, processing systems, and services that must run reliably across development, staging, and production environments. Docker solves the "it works on my machine" problem by packaging code with all its dependencies into reproducible containers. You'll use Docker to:

- Run databases, message queues, and processing engines locally without complex installations
- Build reproducible data pipelines that behave identically across environments
- Deploy microservices and distributed systems in the cloud
- Collaborate with teams using consistent development environments

## Module Contents

### 1. Introduction (~30 min)

- [What is Docker?](01-introduction/01-what-is-docker.md) - The problem Docker solves, containers vs VMs
- [How Docker Works](01-introduction/02-how-docker-works.md) - Architecture, images, containers, layers
- [Docker Across Platforms](01-introduction/03-docker-across-platforms.md) - Linux, macOS, Windows differences

### 2. Working with Docker (~50 min)

- [Images and Dockerfiles](02-working-with-docker/01-images-and-dockerfiles.md) - Building container images
- [Running Containers](02-working-with-docker/02-running-containers.md) - Managing container lifecycle
- [Volumes and Networking](02-working-with-docker/03-volumes-and-networking.md) - Data persistence and container communication

### 3. Docker Compose (~40 min)

- [Compose Fundamentals](03-docker-compose/01-compose-fundamentals.md) - Multi-container orchestration
- [Distributed System Demo](03-docker-compose/02-distributed-system-demo.md) - Gateway + Worker + Redis architecture

### 4. Docker in Practice (~40 min)

- [Registries and Repositories](04-docker-in-practice/01-registries-and-repositories.md) - Sharing images across teams
- [CI/CD and Cloud Deployment](04-docker-in-practice/02-cicd-and-cloud-deployment.md) - Automated pipelines and cloud patterns
- [VSCode Dev Containers](04-docker-in-practice/03-vscode-dev-containers.md) - Consistent development environments

### 5. Hands-on Exercises (~50 min)

- [Containerize a FastAPI App](05-exercises/01-containerize-fastapi-app.md) - Build your first Docker image
- [Build a Distributed System](05-exercises/02-build-a-distributed-system.md) - Multi-service Compose project

## Demo Applications

All materials reference runnable code in the `demo-app/` directory:

- **simple-api/** - A minimal FastAPI application for learning Docker basics
- **distributed-system/** - A complete multi-service system (Gateway + Worker + Redis)

## Learning Path

**For beginners:** Work through sections 1-3 sequentially, then attempt the exercises. Section 4 can be reviewed later when deploying to production.

**For those with Docker experience:** Skim section 1, dive into sections 2-3 for best practices, focus on section 4 for production patterns.

**At Scale:** Throughout the materials, watch for "At Scale" callouts that discuss how concepts apply in production data engineering scenarios with large-scale distributed systems.

## Key Concepts

By the end of this module, you will understand:

- **Images vs Containers** - Blueprints vs running instances
- **Dockerfile layers** - How caching speeds up builds
- **Port mapping** - Connecting to services running inside containers
- **Volumes** - Persisting data beyond container lifetime
- **Docker Compose** - Defining and running multi-container applications
- **Container registries** - Sharing images with your team and CI/CD pipelines
- **Service discovery** - How containers find each other by name

## Best Practices Covered

- Writing efficient Dockerfiles with proper layer ordering
- Using `.dockerignore` to reduce image size
- Multi-stage builds for production images
- Health checks and logging strategies
- Network isolation and security considerations
- Image tagging strategies for CI/CD
- Development workflow with Dev Containers

---

**Next:** [What is Docker?](01-introduction/01-what-is-docker.md)
