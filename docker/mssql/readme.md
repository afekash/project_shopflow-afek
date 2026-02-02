# Running The Container
- Pull the image from the repository
```
docker pull mcr.microsoft.com/mssql/server:2022-latest
```
- Choose a password for the SA user, for example: 61eF92j4VTtl
- Run the container with the password
```
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=61eF92j4VTtl" -p 1433:1433 --name mssql -d mcr.microsoft.com/mssql/server:2022-latest
```

# Restoring AdventureWorks Database From Backup
- Create a directory for the backup
```
docker exec -it mssql mkdir /var/opt/mssql/backup
```
- Download the backup files (regular and dwh) if not already present (Optional)
- Copy the backup files to the container
```
docker cp docker/mssql/data/AdventureWorks2022.bak mssql:/var/opt/mssql/backup/AdventureWorks2022.bak
docker cp docker/mssql/data/AdventureWorksDW2022.bak mssql:/var/opt/mssql/backup/AdventureWorksDW2022.bak
```
- Restore the database
```
docker exec -it mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "61eF92j4VTtl" -C -Q "RESTORE DATABASE AdventureWorks2022 FROM DISK = '/var/opt/mssql/backup/AdventureWorks2022.bak' WITH MOVE 'AdventureWorks2022' TO '/var/opt/mssql/data/AdventureWorks2022.mdf', MOVE 'AdventureWorks2022_log' TO '/var/opt/mssql/data/AdventureWorks2022_log.ldf'"
docker exec -it mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "61eF92j4VTtl" -C -Q "RESTORE DATABASE AdventureWorksDW2022 FROM DISK = '/var/opt/mssql/backup/AdventureWorksDW2022.bak' WITH MOVE 'AdventureWorksDW2022' TO '/var/opt/mssql/data/AdventureWorksDW2022.mdf', MOVE 'AdventureWorksDW2022_log' TO '/var/opt/mssql/data/AdventureWorksDW2022_log.ldf'"
```

# Resoring Northwind Database From SQL Script
- Download the SQL script from the repository if not already present
```
curl -L -o instnwnd.sql https://raw.githubusercontent.com/microsoft/sql-server-samples/master/samples/databases/northwind-pubs/instnwnd.sql
```
- Create a database for the Northwind data
```
docker exec -it mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "61eF92j4VTtl" -C -Q "CREATE DATABASE [Northwind]"
```
- Run the SQL script against the database (from your local machine IDE)