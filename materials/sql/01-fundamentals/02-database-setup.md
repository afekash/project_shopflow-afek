# Database Setup

## Overview

This guide walks you through setting up MS SQL Server 2022 with the Northwind database using Docker. This gives you a consistent, isolated environment perfect for learning SQL.

## Prerequisites

- **Docker Desktop** installed and running
- **SQL Client** - Choose one:
  - [Azure Data Studio](https://docs.microsoft.com/en-us/sql/azure-data-studio/) (recommended, cross-platform)
  - [DBeaver](https://dbeaver.io/) (universal database tool)
  - [VS Code](https://code.visualstudio.com/) with [SQL Server extension](https://marketplace.visualstudio.com/items?itemName=ms-mssql.mssql)
  - SQL Server Management Studio (Windows only)

## Step 1: Pull the SQL Server Image

Open a terminal and pull the official SQL Server 2022 image:

```bash
docker pull mcr.microsoft.com/mssql/server:2022-latest
```

This downloads ~1.5GB, so it may take a few minutes.

## Step 2: Run the Container

Choose a strong password for the `SA` (System Administrator) account. For this course, we'll use: `61eF92j4VTtl`

```bash
docker run -e "ACCEPT_EULA=Y" \
  -e "SA_PASSWORD=61eF92j4VTtl" \
  -p 1433:1433 \
  --name mssql \
  -d mcr.microsoft.com/mssql/server:2022-latest
```

**What this does:**
- `-e "ACCEPT_EULA=Y"` - Accepts Microsoft's license agreement
- `-e "SA_PASSWORD=..."` - Sets the admin password
- `-p 1433:1433` - Maps port 1433 (SQL Server's default) from container to host
- `--name mssql` - Names the container "mssql" for easy reference
- `-d` - Runs in detached mode (background)

**Verify it's running:**

```bash
docker ps
```

You should see the `mssql` container with status "Up".

## Step 3: Prepare the Backup Directory

Create a directory inside the container for database backups:

```bash
docker exec -it mssql mkdir /var/opt/mssql/backup
```

## Step 4: Copy the Northwind Script

The Northwind database is distributed as a SQL script. If you don't have it yet, download it:

```bash
curl -L -o docker/mssql/data/instnwnd.sql \
  https://raw.githubusercontent.com/microsoft/sql-server-samples/master/samples/databases/northwind-pubs/instnwnd.sql
```

Copy it to the container:

```bash
docker cp docker/mssql/data/instnwnd.sql mssql:/var/opt/mssql/backup/
```

## Step 5: Create the Northwind Database

First, create an empty database:

```bash
docker exec -it mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P "61eF92j4VTtl" -C \
  -Q "CREATE DATABASE Northwind"
```

The `-C` flag trusts the server certificate (fine for local development).

## Step 6: Connect with Your SQL Client

Now connect to the database using your preferred client:

**Connection Details:**
- **Server**: `localhost,1433` or `127.0.0.1,1433`
- **Authentication**: SQL Server Authentication
- **Username**: `SA`
- **Password**: `61eF92j4VTtl`
- **Database**: `Northwind`
- **Encrypt**: Optional (or trust server certificate)

## Step 7: Run the Northwind Script

In your SQL client, open the `instnwnd.sql` file and execute it against the `Northwind` database. This creates all tables and populates them with sample data.

Alternatively, run it from the command line:

```bash
docker exec -it mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P "61eF92j4VTtl" -C \
  -d Northwind \
  -i /var/opt/mssql/backup/instnwnd.sql
```

## Step 8: Verify the Installation

Run this query to verify tables were created:

```sql
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
```

You should see tables like `Categories`, `Customers`, `Orders`, `Products`, etc.

Quick sanity check:

```sql
-- Should return 91 customers
SELECT COUNT(*) AS CustomerCount FROM Customers;

-- Should return 830 orders
SELECT COUNT(*) AS OrderCount FROM Orders;

-- Should return 77 products
SELECT COUNT(*) AS ProductCount FROM Products;
```

## Managing the Container

**Stop the container:**

```bash
docker stop mssql
```

**Start it again:**

```bash
docker start mssql
```

**Remove the container** (you'll lose all data!):

```bash
docker stop mssql
docker rm mssql
```

**View logs** (useful for troubleshooting):

```bash
docker logs mssql
```

## Advanced Insight: Why Docker?

Docker provides several advantages for learning environments:

1. **Consistency** - Everyone has the exact same setup
2. **Isolation** - Doesn't interfere with other software on your machine
3. **Reproducibility** - Can destroy and recreate instantly
4. **Version control** - Pin exact database versions
5. **Resource limits** - Can constrain memory/CPU to simulate production constraints

In production environments:
- **Managed database services** (Cloud SQL, AWS RDS, Azure SQL Database) are preferred over containerized databases
- **Dedicated machines** with persistent storage are common for on-premise SQL instances
- **Why not containers for databases?**
  - Databases require **persistent, reliable storage** - container orchestration platforms may move/restart containers
  - **Performance**: Containers add overhead; databases need direct access to storage I/O
  - **Backup/recovery**: Managed services handle automated backups, point-in-time recovery, high availability
  - **Maintenance**: Patching, upgrades, monitoring are managed by the cloud provider
- Containers **are** used for stateless services (APIs, ETL workers, microservices)

## Troubleshooting

### Container won't start

Check if port 1433 is already in use:

```bash
# macOS/Linux
lsof -i :1433

# Windows
netstat -ano | findstr :1433
```

If something else is using it, either stop that service or map to a different port:

```bash
docker run -e "ACCEPT_EULA=Y" \
  -e "SA_PASSWORD=61eF92j4VTtl" \
  -p 1444:1433 \
  --name mssql \
  -d mcr.microsoft.com/mssql/server:2022-latest
```

Then connect to `localhost,1444` instead.

### Password doesn't meet requirements

SQL Server requires strong passwords:
- At least 8 characters
- Uppercase, lowercase, digits, and symbols
- Example: `MyStr0ng!Pass`

### Can't connect from client

1. Ensure container is running: `docker ps`
2. Check container logs: `docker logs mssql`
3. Verify firewall isn't blocking port 1433
4. Try using IP `127.0.0.1` instead of `localhost`

## Optional: AdventureWorks Databases

The course repository also includes AdventureWorks databases (OLTP and DW versions). To use them:

```bash
# Copy backups
docker cp docker/mssql/data/AdventureWorks2022.bak mssql:/var/opt/mssql/backup/
docker cp docker/mssql/data/AdventureWorksDW2022.bak mssql:/var/opt/mssql/backup/

# Restore OLTP database
docker exec -it mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "61eF92j4VTtl" -C -Q \
"RESTORE DATABASE AdventureWorks2022 FROM DISK = '/var/opt/mssql/backup/AdventureWorks2022.bak' \
WITH MOVE 'AdventureWorks2022' TO '/var/opt/mssql/data/AdventureWorks2022.mdf', \
MOVE 'AdventureWorks2022_log' TO '/var/opt/mssql/data/AdventureWorks2022_log.ldf'"

# Restore Data Warehouse
docker exec -it mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "61eF92j4VTtl" -C -Q \
"RESTORE DATABASE AdventureWorksDW2022 FROM DISK = '/var/opt/mssql/backup/AdventureWorksDW2022.bak' \
WITH MOVE 'AdventureWorksDW2022' TO '/var/opt/mssql/data/AdventureWorksDW2022.mdf', \
MOVE 'AdventureWorksDW2022_log' TO '/var/opt/mssql/data/AdventureWorksDW2022_log.ldf'"
```

These provide more complex schemas for advanced topics.

## Key Takeaways

- Docker provides consistent, isolated database environments
- Northwind is installed via SQL script (DDL + INSERT statements)
- Containers can be started/stopped without losing data (unless removed)

## What's Next?

Now that your database is set up, let's understand how SQL queries are processed:

[Next: SQL Execution Order →](03-sql-execution-order.md)

---

[← Back: Introduction](01-introduction.md) | [Course Home](../README.md) | [Next: SQL Execution Order →](03-sql-execution-order.md)
