#!/bin/bash
# Initialize a 3-node MongoDB replica set
# Run AFTER docker compose up -d
#
# PREREQUISITE — add to /etc/hosts (macOS/Linux) so the replica set member
# hostnames resolve to localhost from the host machine:
#   sudo sh -c 'echo "127.0.0.1 mongo1 mongo2 mongo3" >> /etc/hosts'
#
# On Windows, add the same line to:
#   C:\Windows\System32\drivers\etc\hosts  (open Notepad as Administrator)

set -e

echo "Waiting for MongoDB nodes to be ready..."
sleep 3

echo "Initiating replica set rs0..."
docker exec mongo1 mongosh --port 27017 --eval "
rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: 'mongo1:27017', priority: 2 },
    { _id: 1, host: 'mongo2:27018', priority: 1 },
    { _id: 2, host: 'mongo3:27019', priority: 1 }
  ]
})
"

echo "Waiting for election to complete..."
sleep 5

echo "Checking replica set status..."
docker exec mongo1 mongosh --port 27017 --eval "rs.status().members.map(m => ({name: m.name, state: m.stateStr}))"

echo "Inserting test data on the primary..."
docker exec mongo1 mongosh --port 27017 --eval "
use demo
db.products.insertMany([
  { sku: 'LAPTOP-001', name: 'Laptop Pro 15', category: 'electronics', price: 1299.99, stock: 45 },
  { sku: 'MOUSE-001',  name: 'Wireless Mouse', category: 'electronics', price: 29.99, stock: 200 },
  { sku: 'KBOARD-001', name: 'Mechanical Keyboard', category: 'electronics', price: 149.99, stock: 75 },
  { sku: 'SHIRT-001',  name: 'Cotton T-Shirt', category: 'clothing', price: 19.99, stock: 500 },
  { sku: 'DESK-001',   name: 'Standing Desk', category: 'furniture', price: 599.99, stock: 20 }
])
print('Inserted ' + db.products.countDocuments() + ' products')
"

echo ""
echo "====================================================="
echo "Replica set is ready!"
echo ""
echo "Connection strings:"
echo "  Primary (mongo1):    mongosh 'mongodb://localhost:27017'"
echo "  Secondary (mongo2):  mongosh 'mongodb://localhost:27018'"
echo "  Secondary (mongo3):  mongosh 'mongodb://localhost:27019'"
echo ""
echo "Replica set URI:"
echo "  mongosh 'mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0'"
echo "====================================================="
