# ─── John Bryce Data Engineering Teaching Platform ──────────────────────────
#
# Convention:
#   make docs           — workspace only (MyST site + Jupyter, no sidecars)
#   make lab-<name>     — workspace + lesson-specific sidecar services
#   make down           — stop whichever lab is currently running
#   make reset          — stop and remove all containers, networks, and volumes
#   make shell          — open a bash shell in the running workspace container
#
# Lab architecture:
#   Every lab merges labs/base/compose.yml (workspace) with labs/<name>/compose.yml
#   (sidecars + workspace overrides). The LAB build arg installs per-lab Python deps.
# ────────────────────────────────────────────────────────────────────────────

.PHONY: docs lab-orm lab-sql lab-nosql lab-replica-set lab-sharded lab-distributed lab-web \
        down reset shell convert \
        replica-set-init sharded-init sql-restore \
        help

BASE := -f labs/base/compose.yml

# ─── Default target ─────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  make docs                 Start workspace only (MyST docs + Jupyter)"
	@echo "  make lab-orm              Start workspace + PostgreSQL (ORM lesson)"
	@echo "  make lab-sql              Start workspace + MSSQL (SQL lesson)"
	@echo "  make lab-nosql            Start workspace + standalone MongoDB"
	@echo "  make lab-replica-set      Start workspace + 3-node MongoDB replica set"
	@echo "  make lab-sharded          Start workspace + MongoDB sharded cluster"
	@echo "  make lab-distributed      Start workspace + gateway + worker + Redis"
	@echo "  make lab-web              Start workspace with FastAPI deps (Web APIs lesson)"
	@echo ""
	@echo "  make down                 Stop the running lab"
	@echo "  make reset                Stop + remove all containers and volumes"
	@echo "  make shell                Open bash in the workspace container"
	@echo ""
	@echo "  make replica-set-init     Initialize MongoDB replica set (after lab-replica-set)"
	@echo "  make sharded-init         Initialize MongoDB sharded cluster (after lab-sharded)"
	@echo "  make sql-restore          Restore AdventureWorks/Northwind databases (after lab-sql)"
	@echo ""
	@echo "  make convert FILE=path    Convert a MyST lesson to py:percent (instructor only)"
	@echo ""

# ─── Docs / workspace only ──────────────────────────────────────────────────

docs:
	docker compose $(BASE) up -d --build
	@echo "MyST docs: http://localhost:3000"
	@echo "Jupyter:   http://localhost:8888"

# ─── Lab environments ───────────────────────────────────────────────────────

lab-orm:
	docker compose $(BASE) -f labs/orm/compose.yml up -d --build
	@echo "PostgreSQL available at localhost:5432"
	@echo "MyST docs: http://localhost:3000"

lab-sql:
	docker compose $(BASE) -f labs/sql/compose.yml up -d --build
	@echo "MSSQL available at localhost:1433 (SA / see .env or default password)"
	@echo "Run 'make sql-restore' to restore AdventureWorks and Northwind databases."
	@echo "MyST docs: http://localhost:3000"

lab-nosql:
	docker compose $(BASE) -f labs/nosql/compose.yml up -d --build
	@echo "MongoDB available at localhost:27017"
	@echo "MyST docs: http://localhost:3000"

lab-replica-set:
	docker compose $(BASE) -f labs/replica-set/compose.yml up -d --build
	@echo "Waiting for Mongo nodes to start..."
	sleep 5
	$(MAKE) replica-set-init
	@echo "MyST docs: http://localhost:3000"

lab-sharded:
	docker compose $(BASE) -f labs/sharded/compose.yml up -d --build
	@echo "Waiting for cluster nodes to start..."
	sleep 10
	$(MAKE) sharded-init
	@echo "MyST docs: http://localhost:3000"

lab-distributed:
	docker compose $(BASE) -f labs/distributed/compose.yml up -d --build
	@echo "Gateway API: http://localhost:8000"
	@echo "Redis:       localhost:6379"
	@echo "MyST docs:   http://localhost:3000"

lab-web:
	docker compose $(BASE) -f labs/web/compose.yml up -d --build
	@echo "MyST docs: http://localhost:3000"

# ─── Common operations ──────────────────────────────────────────────────────

down:
	@for d in labs/*/; do \
		f="$$d/compose.yml"; \
		[ -f "$$f" ] && docker compose $(BASE) -f "$$f" down 2>/dev/null || true; \
	done
	docker compose $(BASE) down 2>/dev/null || true

reset:
	@for d in labs/*/; do \
		f="$$d/compose.yml"; \
		[ -f "$$f" ] && docker compose $(BASE) -f "$$f" down -v --remove-orphans 2>/dev/null || true; \
	done
	docker compose $(BASE) down -v --remove-orphans 2>/dev/null || true

shell:
	docker exec -it $$(docker ps --filter "name=workspace" -q | head -1) bash

# ─── Lab-specific helpers ────────────────────────────────────────────────────

replica-set-init:
	bash labs/replica-set/init.sh

sharded-init:
	bash labs/sharded/init.sh

sql-restore:
	bash labs/sql/restore.sh

# ─── Instructor convenience ──────────────────────────────────────────────────

convert:
	@[ -n "$(FILE)" ] || (echo "Usage: make convert FILE=materials/python/01-orm/01-lesson.md" && exit 1)
	jupytext --from md:myst --to py:percent $(FILE)
	@echo "Created $$(echo $(FILE) | sed 's/\.md$$/.py/')"
	@echo "Remember: discard this file after use -- it is not the source of truth."
