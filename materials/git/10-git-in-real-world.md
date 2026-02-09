# Git in the Real World

## Overview

How do real companies use Git? This lesson covers enterprise workflows, CI/CD pipelines, GitHub Actions, and how Git fits into data engineering specifically.

**Duration:** ~15 minutes

## How Companies Use Git

### Repository Strategies

#### Monorepo (Single Repository)

All code in one repository:

```
company-repo/
├── frontend/
├── backend/
├── data-pipelines/
├── infrastructure/
└── shared-libraries/
```

**Examples:** Google, Facebook, Microsoft (for some products)

**Pros:**
- Easy code sharing
- Atomic changes across projects
- Unified tooling

**Cons:**
- Large repo size
- Complex CI/CD
- Requires special tools (Bazel, Nx)

#### Multi-repo (Microservices)

Separate repository per service:

```
user-service/
payment-service/
analytics-service/
data-warehouse/
```

**Pros:**
- Independent deployments
- Clear ownership
- Smaller repos

**Cons:**
- Dependency management
- Cross-repo changes harder
- More overhead

### Branch Strategies

#### GitHub Flow (Simple)

```
main (always deployable)
  ↓
feature branches → PR → merge
  ↓
deploy
```

**Best for:** Small teams, continuous deployment, web apps

#### Git Flow (Complex)

```
main (production)
  ↓
develop (integration)
  ↓
feature branches
  ↓
release branches
  ↓
hotfix branches
```

**Best for:** Scheduled releases, enterprise software

#### Trunk-Based Development

```
main (trunk)
  ↓
short-lived branches (< 1 day)
  ↓
merge quickly
  ↓
feature flags for incomplete work
```

**Best for:** Large teams, very frequent integration

### Protected Branches

Companies enforce rules on `main`:

```
Required:
✓ Pull request before merging
✓ 2 approvals required
✓ All CI checks pass
✓ Branch up to date
✓ No force pushes
✓ Require signed commits
```

**Why:** Prevent accidental breaks, enforce code quality.

## CI/CD Fundamentals

### What is CI/CD?

**Continuous Integration (CI):**
- Automatically build and test code on every push
- Catch bugs early
- Ensure code integrates cleanly

**Continuous Deployment (CD):**
- Automatically deploy passing code
- Reduce manual errors
- Ship faster

### The CI/CD Pipeline

```
Developer pushes code
       ↓
  Git triggers
       ↓
   Build code
       ↓
   Run tests
       ↓
   Lint/format check
       ↓
   Security scan
       ↓
   Deploy to staging
       ↓
   Run integration tests
       ↓
   Deploy to production
```

### Where Git Fits In

```
git push → GitHub → Webhook → CI/CD Platform
                                    ↓
                            Build → Test → Deploy
```

**Git triggers everything.**

## GitHub Actions Basics

### What are GitHub Actions?

Built-in CI/CD for GitHub:
- Runs workflows on git events (push, PR, tag)
- Free for public repos
- Integrated with GitHub

### Simple Example: Run Tests

```yaml
# .github/workflows/test.yml
name: Run Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=src tests/
    
    - name: Lint code
      run: |
        flake8 src/
```

**What this does:**
- Triggers on push to main or PR
- Sets up Python environment
- Installs dependencies
- Runs tests with coverage
- Lints code

### Data Pipeline Example

```yaml
# .github/workflows/data-pipeline.yml
name: Data Pipeline Tests

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install pandas sqlalchemy pytest
    
    - name: Run ETL tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test
      run: |
        pytest tests/test_etl.py
    
    - name: Validate SQL migrations
      run: |
        python scripts/validate_migrations.py
```

**Advanced features:**
- Spins up PostgreSQL for testing
- Tests ETL pipeline
- Validates SQL migrations

### Deploy on Tag

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        echo "Deploying version ${{ github.ref_name }}"
        # Deploy commands here
```

**Triggered by:**

```bash
# Create and push a tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Git in Data Engineering

### What Data Engineers Version Control

#### 1. SQL Migrations

```
migrations/
├── 001_create_users_table.sql
├── 002_add_email_column.sql
├── 003_create_orders_table.sql
└── 004_add_index_on_user_id.sql
```

**Best practices:**
- Timestamp or number prefix
- One-way migrations (create, alter, not drop)
- Test on staging first

#### 2. dbt Projects

```
dbt-project/
├── models/
│   ├── staging/
│   │   ├── stg_users.sql
│   │   └── stg_orders.sql
│   ├── intermediate/
│   └── marts/
├── tests/
├── macros/
└── dbt_project.yml
```

**Why Git matters:**
- Track model changes
- Code review transformations
- Rollback bad changes
- CI/CD for testing

#### 3. Airflow DAGs

```
airflow/
├── dags/
│   ├── daily_etl.py
│   ├── weekly_report.py
│   └── user_segmentation.py
├── plugins/
├── config/
└── tests/
```

**Git workflow:**
- Branch per DAG feature
- Test DAGs in dev environment
- Review before deploying
- Version control connections/variables

#### 4. Data Pipeline Configs

```
pipelines/
├── extract_configs/
│   ├── salesforce.yaml
│   └── postgres.yaml
├── transform_configs/
└── load_configs/
```

**Why version control:**
- Track configuration changes
- Audit who changed what
- Rollback broken configs
- Environment-specific configs (dev/prod)

### Data Engineering Git Workflow

```bash
# 1. Branch for new pipeline
git switch -c feature/add-customer-pipeline

# 2. Develop pipeline
cat > dags/customer_etl.py << EOF
from airflow import DAG
# ... pipeline code ...
EOF

# 3. Add tests
cat > tests/test_customer_etl.py << EOF
def test_extract():
    # ...
EOF

# 4. Commit atomically
git add dags/customer_etl.py
git commit -m "Add customer data extraction"

git add tests/test_customer_etl.py
git commit -m "Add tests for customer ETL"

# 5. Push and PR
git push -u origin feature/add-customer-pipeline

# 6. CI runs tests automatically
# 7. Code review
# 8. Merge to main
# 9. CD deploys to Airflow
```

### dbt + Git Example

```bash
# 1. Create dbt model branch
git switch -c feature/customer-segmentation

# 2. Create model
cat > models/marts/customer_segments.sql << EOF
with customer_stats as (
    select 
        user_id,
        count(*) as order_count,
        sum(total) as lifetime_value
    from {{ ref('stg_orders') }}
    group by user_id
)
select
    user_id,
    case 
        when lifetime_value > 1000 then 'high_value'
        when lifetime_value > 500 then 'medium_value'
        else 'low_value'
    end as segment
from customer_stats
EOF

# 3. Add test
cat > models/marts/customer_segments.yml << EOF
version: 2
models:
  - name: customer_segments
    columns:
      - name: user_id
        tests:
          - not_null
          - unique
      - name: segment
        tests:
          - accepted_values:
              values: ['high_value', 'medium_value', 'low_value']
EOF

# 4. Run locally
dbt run --models customer_segments
dbt test --models customer_segments

# 5. Commit and push
git add models/marts/customer_segments.*
git commit -m "Add customer segmentation model

- Segments customers by lifetime value
- Added data quality tests
- Depends on stg_orders model"

git push -u origin feature/customer-segmentation

# 6. PR triggers CI
# - Runs dbt compile
# - Runs dbt test
# - Checks SQL lint

# 7. After merge, CD deploys to production dbt
```

## Best Practices for Data Teams

### 1. Never Commit Data

```bash
# .gitignore
data/raw/*.csv
data/processed/*.parquet
*.db
*.sqlite
datasets/
```

**Why:** 
- Git is for code, not data
- Data lakes/warehouses are for data
- Large files slow down Git

### 2. Version Control Schema Changes

```sql
-- migrations/005_add_user_preferences.sql
-- Author: Jane Doe
-- Date: 2026-02-09
-- Description: Add user preferences table

CREATE TABLE user_preferences (
    user_id INT PRIMARY KEY,
    theme VARCHAR(20),
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_prefs_user_id ON user_preferences(user_id);
```

### 3. Atomic Pipeline Commits

```bash
# Bad: one giant commit
git commit -m "Add entire pipeline"

# Good: small focused commits
git commit -m "Add S3 extraction logic"
git commit -m "Add data transformation step"
git commit -m "Add warehouse loading logic"
git commit -m "Add error handling and retries"
git commit -m "Add tests for pipeline"
```

### 4. Use Conventional Commits

```bash
feat: add customer segmentation model
fix: correct date parsing in ETL
docs: update data dictionary
test: add integration tests for pipeline
refactor: extract common SQL to macro
chore: update dbt dependencies
```

**Why:** Clear history, automated changelogs, semantic versioning.

### 5. Protect Production Branches

```
main (production) → requires 2 approvals
develop (staging) → requires 1 approval
feature/* → no restrictions
```

## At Scale: Enterprise Patterns

### Monorepo with Bazel (Google-style)

- Single repo with millions of files
- Selective checkout
- Cached builds
- Hermetic testing

### Trunk-Based with Feature Flags

```python
# Code is always merged to main
# Incomplete features hidden behind flags

if feature_flag('new_algorithm'):
    use_new_algorithm()
else:
    use_old_algorithm()
```

**Benefits:**
- No long-lived branches
- Continuous integration
- Deploy anytime

### Git Hooks for Data Quality

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Run before every commit

# Validate SQL syntax
sqlfluff lint sql/*.sql

# Check dbt models compile
dbt compile

# Run fast tests
pytest tests/unit/
```

## Key Takeaways

1. **Companies enforce Git standards** - Branch protection, required reviews
2. **CI/CD triggered by Git** - Push → build → test → deploy
3. **GitHub Actions** - Built-in CI/CD for GitHub repos
4. **Data engineers version control** - SQL, dbt, Airflow, configs
5. **Never commit data** - Only code and configs
6. **Atomic commits** - Small, focused changes
7. **Conventional commits** - Structured commit messages

## Best Practices

1. **Branch protection** - Require PRs and reviews
2. **Automated testing** - CI runs on every PR
3. **Version migrations** - Track schema changes
4. **Small commits** - Easier to review and revert
5. **Clear messages** - Use conventional commit format
6. **Never commit secrets** - Use environment variables

## What's Next?

You now understand how Git is used in production. Next, you'll learn about **VSCode Git integration**—how to use Git through your IDE for a faster workflow.

---

**Navigation:**
- **Previous:** [09 - GitHub Workflow](09-github-workflow.md)
- **Next:** [11 - VSCode Git Guide](11-vscode-git-guide.md)
- **Home:** [Git Course Overview](README.md)
