#!/usr/bin/env bash
set -euo pipefail

echo "Initializing MongoDB replica set rs0..."

docker exec mongo1 mongosh --port 27017 --quiet --eval \
  'rs.initiate({
    _id: "rs0",
    members: [
      { _id: 0, host: "mongo1:27017" },
      { _id: 1, host: "mongo2:27018" },
      { _id: 2, host: "mongo3:27019" }
    ]
  })'

echo "Replica set rs0 initialized. Primary on mongo1:27017"
