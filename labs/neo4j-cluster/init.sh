#!/usr/bin/env bash
# Initialize Neo4j Causal Cluster: wait for all cores to form the cluster, then seed data.
# Run after: make lab-neo4j-cluster
# Called automatically by: make neo4j-cluster-init

set -e

COMPOSE="docker compose -f labs/base/compose.yml -f labs/neo4j-cluster/compose.yml"

echo "Waiting for Neo4j cluster members to be ready..."
for core in neo4j-core1 neo4j-core2 neo4j-core3; do
  echo -n "  $core: "
  until $COMPOSE exec -T "$core" wget -qO- http://localhost:7474 > /dev/null 2>&1; do
    sleep 3
  done
  echo "ready"
done

echo ""
echo "Waiting for cluster to form and neo4j database to accept writes..."
until $COMPOSE exec -T neo4j-core1 cypher-shell \
    -u neo4j -p password --database neo4j \
    "RETURN 1" \
    > /dev/null 2>&1; do
  sleep 3
done
echo "Cluster ready — neo4j database accepting connections."

echo ""
echo "Seeding dataset via cluster routing..."
# Find which container is currently hosting the neo4j database writer and
# exec into it directly — avoids the routing table lookup that fails on
# non-hosting nodes.
WRITER_ADDR=$($COMPOSE exec -T neo4j-core1 cypher-shell \
  -u neo4j -p password --database system \
  "SHOW DATABASES YIELD name, address, writer WHERE name='neo4j' AND writer=true" \
  2>/dev/null | grep '"neo4j"' | grep -o '"neo4j-core[^"]*"' | head -1 | tr -d '"')
WRITER_HOST=$(echo "$WRITER_ADDR" | cut -d: -f1)
echo "  Writing via: $WRITER_HOST"

$COMPOSE exec -T "$WRITER_HOST" cypher-shell \
  -u neo4j -p password \
  --database neo4j \
  "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;"

$COMPOSE exec -T "$WRITER_HOST" cypher-shell \
  -u neo4j -p password \
  --database neo4j \
  "
  MERGE (alice:Person {id: 1, name: 'Alice', city: 'New York'})
  MERGE (bob:Person   {id: 2, name: 'Bob',   city: 'London'})
  MERGE (carol:Person {id: 3, name: 'Carol', city: 'New York'})
  MERGE (dave:Person  {id: 4, name: 'Dave',  city: 'London'})
  MERGE (alice)-[:KNOWS {since: 2020}]->(bob)
  MERGE (alice)-[:KNOWS {since: 2021}]->(carol)
  MERGE (bob)-[:KNOWS   {since: 2019}]->(dave)
  MERGE (carol)-[:KNOWS {since: 2022}]->(dave);
  "

echo ""
echo "Neo4j Cluster is ready."
echo "Core members: neo4j-core1:7687, neo4j-core2:7688, neo4j-core3:7689"
echo "Connect from workspace: bolt://neo4j-core1:7687 (routing), auth neo4j/password"
