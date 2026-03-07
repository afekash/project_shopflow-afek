---
title: Data Engineering Course
---

# Welcome to the Data Engineering Course

A hands-on, self-served teaching platform covering databases, distributed systems, Python, and DevOps for data engineers.

## How to Use This Site

Each lesson is an interactive page — code cells can be executed directly in the browser via the embedded Jupyter kernel. No local Python setup needed.

:::{note}
Some lessons require sidecar services (databases, clusters). Run `make lab-<name>` from the workspace terminal before starting those lessons.
:::


## Quick Lab Reference

| Command | Environment |
|---------|-------------|
| `make docs` | Docs + Jupyter only |
| `make lab-orm` | + PostgreSQL |
| `make lab-sql` | + SQL Server |
| `make lab-nosql` | + MongoDB |
| `make lab-replica-set` | + MongoDB replica set |
| `make lab-sharded` | + MongoDB sharded cluster |
| `make lab-distributed` | + gateway, worker, Redis |

Run `make down` to stop the current lab before switching.
