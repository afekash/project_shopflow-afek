# Docker Across Platforms

## Overview

Docker runs on Linux, macOS, and Windows, but the underlying implementation differs significantly across platforms. Understanding these differences helps you troubleshoot issues and optimize performance.

In this section, we'll explore how Docker works natively on Linux, how it adapts to macOS and Windows, and the practical implications for your workflow.

## Linux: Docker's Native Home

Containers are a Linux technology. Docker on Linux runs directly on the host kernel without any virtualization layer.

### How It Works

```
Linux Host
├── Kernel (provides namespaces, cgroups)
└── Docker Engine
    ├── Container 1 (isolated process)
    ├── Container 2 (isolated process)
    └── Container 3 (isolated process)
```

**Key points:**
- Containers share the Linux kernel with the host
- No VM layer—containers are just isolated processes
- Native performance (near-zero overhead)
- Direct filesystem access (fast I/O)

**Installation:** On Ubuntu, you install Docker Engine directly:
```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

**Performance:** This is the **fastest** way to run Docker. If you're deploying containers in production, they'll almost certainly run on Linux (bare metal or cloud VMs).

### Linux Distributions in Containers

Even though containers share the host kernel, each container can use a different Linux distribution's userland tools:

```bash
# Container 1: Ubuntu-based
docker run -it ubuntu:22.04 bash
$ cat /etc/os-release
# Shows "Ubuntu 22.04"

# Container 2: Alpine-based
docker run -it alpine:3.18 sh
$ cat /etc/os-release
# Shows "Alpine Linux 3.18"
```

**Why this works:** The distribution (Ubuntu, Alpine, Debian) is just a set of userland tools (shell, package manager, libraries) bundled on top of the shared kernel. The kernel itself is the host's Linux kernel.

**Limitation:** You cannot run a Windows container on a Linux host (they require different kernels).

## macOS: Docker Desktop with Virtualization

macOS does not have native container support because macOS is not Linux. Docker Desktop for Mac runs a lightweight Linux VM to host the Docker Engine.

### How It Works

```
macOS Host
└── Docker Desktop
    └── Lightweight Linux VM (using Apple Virtualization Framework)
        └── Docker Engine
            ├── Container 1
            ├── Container 2
            └── Container 3
```

**Key technologies:**
- **Virtualization Framework:** macOS's native hypervisor (since macOS 10.15 Catalina)
- **VirtioFS:** Filesystem sharing between macOS and the VM (for volume mounts)

**Installation:** Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop) and install the GUI application.

### Practical Implications

**1. Filesystem Performance**

When you bind-mount a directory from macOS into a container, Docker shares files between macOS and the Linux VM using VirtioFS. This adds overhead.

```bash
# Mounting a local directory
docker run -v $(pwd):/app myimage

# File I/O is slower than on native Linux
# Reads/writes go through: Container -> VM -> macOS filesystem
```

**Impact on data engineering:**
- Reading/writing large datasets from mounted volumes is **slower** than on Linux
- For heavy I/O, consider using Docker volumes (stored inside the VM) or copying data into the image

**2. Networking**

Containers run inside the VM, not directly on macOS. Port forwarding is handled automatically by Docker Desktop:

```bash
docker run -p 8000:8000 myapp

# Docker Desktop forwards localhost:8000 (macOS) to container:8000 (inside VM)
```

This usually works seamlessly, but edge cases exist (e.g., binding to specific network interfaces).

**3. Memory and CPU Limits**

Docker Desktop allocates a fixed amount of macOS resources to the VM (configurable in Docker Desktop settings). Containers share this allocation.

```
macOS: 16 GB RAM, 8 CPUs
└── Docker Desktop VM: 4 GB RAM, 4 CPUs (configured)
    └── Containers share the 4 GB / 4 CPUs
```

**Best Practice:** Adjust Docker Desktop resource limits in **Preferences > Resources** based on your needs.

### Advanced: Docker Desktop Architecture

Docker Desktop for Mac includes:
- **Linux VM:** Runs Docker Engine (you don't SSH into it—it's managed transparently)
- **Docker CLI:** Installed on macOS, communicates with the Docker Engine in the VM
- **VirtioFS:** Fast filesystem sharing
- **OSXFS (legacy):** Older filesystem sharing (slower, replaced by VirtioFS in newer versions)

You interact with Docker as if it were native—the VM is invisible in normal use.

## Windows: Two Modes—Linux and Windows Containers

Docker Desktop for Windows supports **two types of containers:**
1. **Linux containers** (default, most common)
2. **Windows containers** (for Windows-specific apps)

### Linux Containers on Windows (WSL 2 Backend)

This is the default mode. Docker Desktop runs a Linux VM using **WSL 2** (Windows Subsystem for Linux version 2).

```
Windows 10/11
└── WSL 2 (lightweight Linux kernel managed by Windows)
    └── Docker Engine
        ├── Container 1 (Linux)
        ├── Container 2 (Linux)
        └── Container 3 (Linux)
```

**How it works:**
- WSL 2 is a full Linux kernel running inside a lightweight VM
- Docker Engine runs in WSL 2, not directly on Windows
- Containers are Linux containers (Ubuntu, Alpine, etc.)

**Installation:**
1. Enable WSL 2 in Windows Features
2. Install Docker Desktop, select "Use the WSL 2 based engine"

**Filesystem performance:**
- **Fast:** When working inside WSL 2 (`/home/user` in WSL)
- **Slow:** When bind-mounting from Windows filesystem (`C:\Users\...`) due to cross-system file sharing

**Best Practice on Windows:** Keep your project files inside the WSL 2 filesystem for better performance:
```bash
# Inside WSL 2 terminal
cd ~
git clone https://github.com/yourproject.git
cd yourproject
docker build -t myapp .
# Much faster than working from /mnt/c/Users/...
```

### Windows Containers (Native Windows)

Windows containers run Windows applications (e.g., .NET Framework apps, IIS web servers). They require a Windows host and use the Windows kernel.

```
Windows Server or Windows 10/11 Pro
└── Docker Engine (Windows mode)
    ├── Container 1 (Windows Server Core)
    ├── Container 2 (Nano Server)
    └── Container 3 (Windows app)
```

**Switching between modes:**

Docker Desktop can switch between Linux and Windows containers:
```
Docker Desktop > Settings > Switch to Windows containers
```

**When to use Windows containers:**
- You need to run .NET Framework applications (not .NET Core, which runs on Linux)
- You need Windows-specific features (IIS, Windows authentication)

**Limitation:** Windows containers are **much larger** than Linux containers (Windows Server Core base image is ~2 GB vs. Alpine Linux at ~5 MB).

**In data engineering:** You'll almost always use Linux containers. Windows containers are rare outside of legacy enterprise Windows workloads.

## Comparison Table

| Aspect | Linux | macOS | Windows (WSL 2) | Windows (Native) |
|--------|-------|-------|-----------------|------------------|
| **Docker runs on** | Native kernel | Linux VM | Linux VM (WSL 2) | Windows kernel |
| **Container type** | Linux | Linux | Linux | Windows |
| **Filesystem performance** | Fast | Slower (VirtioFS) | Fast (in WSL), slow (from Windows) | Fast |
| **Performance overhead** | None | Low (VM overhead) | Low (VM overhead) | None |
| **Installation** | Docker Engine | Docker Desktop | Docker Desktop | Docker Desktop |
| **Best for production** | Yes | No (dev only) | No (dev only) | Rare (Windows apps) |

## Practical Recommendations

### For Development

**On Linux:**
- Use Docker Engine (no Docker Desktop needed)
- Enjoy native performance
- Ideal for data engineering workloads with large datasets

**On macOS:**
- Use Docker Desktop (only option)
- Be mindful of bind-mount performance—use volumes for heavy I/O
- Consider using Docker Compose volumes instead of bind mounts for databases

**On Windows:**
- Use Docker Desktop with WSL 2 backend
- Keep project files in WSL 2 filesystem (`~/projects/` not `/mnt/c/`)
- Use a WSL-aware terminal (Windows Terminal, VS Code's WSL extension)

### For Production

**Always Linux.** Production containers run on:
- Linux VMs in the cloud (AWS EC2, Google Compute Engine, Azure VMs)
- Managed container services (AWS ECS/Fargate, Google Cloud Run, Azure Container Instances)
- Kubernetes clusters (EKS, GKE, AKS)

You develop on macOS/Windows, but deploy to Linux. Docker's "build once, run anywhere" promise means the same image works on all platforms (as long as the container type matches—Linux containers on Linux hosts).

## At Scale: Cross-Platform Builds

When building images on macOS/Windows but deploying to Linux, ensure you're building for the correct architecture:

**Problem:** Apple Silicon Macs (M1, M2, M3) use ARM64 architecture. Production servers often use x86_64 (AMD/Intel).

**Solution:** Build multi-platform images:
```bash
# Build for both ARM64 (Mac) and x86_64 (production servers)
docker buildx build --platform linux/amd64,linux/arm64 -t myimage:latest .
```

Docker Buildx creates images that work on both architectures. Cloud registries (Docker Hub, ECR) store multi-architecture manifests, so `docker pull` automatically fetches the correct variant.

**Best Practice:** In CI/CD pipelines, always build for `linux/amd64` (or both) to ensure compatibility with production environments.

## Summary

Docker runs natively on Linux with zero overhead. On macOS and Windows, Docker Desktop uses a lightweight VM to run the Docker Engine, introducing minor performance trade-offs (especially for filesystem I/O). Linux containers are the default and most common; Windows containers exist for legacy Windows applications. For production, always use Linux hosts.

**Key Takeaways:**
- **Linux:** Native performance, no VM layer
- **macOS:** Docker Desktop uses a Linux VM, slower bind-mount I/O
- **Windows (WSL 2):** Similar to macOS, fast when working inside WSL filesystem
- **Windows containers:** Rare, used only for Windows-specific apps
- **Production:** Always Linux, often on cloud platforms or Kubernetes

---

**Previous:** [How Docker Works](02-how-docker-works.md) | **Next:** [Images and Dockerfiles](../02-working-with-docker/01-images-and-dockerfiles.md)
