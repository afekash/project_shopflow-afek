#!/usr/bin/env bash
set -euo pipefail

SA_PASSWORD="${SA_PASSWORD:-61eF92j4VTtl}"

echo "Restoring AdventureWorks2022..."
docker exec mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA \
  -P "${SA_PASSWORD}" -C \
  -Q "RESTORE DATABASE AdventureWorks2022 FROM DISK = '/var/opt/mssql/backup/AdventureWorks2022.bak'
      WITH MOVE 'AdventureWorks2022'     TO '/var/opt/mssql/data/AdventureWorks2022.mdf',
           MOVE 'AdventureWorks2022_log' TO '/var/opt/mssql/data/AdventureWorks2022_log.ldf'"

echo "Restoring AdventureWorksDW2022..."
docker exec mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA \
  -P "${SA_PASSWORD}" -C \
  -Q "RESTORE DATABASE AdventureWorksDW2022 FROM DISK = '/var/opt/mssql/backup/AdventureWorksDW2022.bak'
      WITH MOVE 'AdventureWorksDW2022'     TO '/var/opt/mssql/data/AdventureWorksDW2022.mdf',
           MOVE 'AdventureWorksDW2022_log' TO '/var/opt/mssql/data/AdventureWorksDW2022_log.ldf'"

echo "Restoring Northwind..."
docker exec mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA \
  -P "${SA_PASSWORD}" -C \
  -Q "CREATE DATABASE [Northwind]"
docker exec -i mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA \
  -P "${SA_PASSWORD}" -C -d Northwind \
  -i /var/opt/mssql/backup/instnwnd.sql

echo "Database restore complete."
