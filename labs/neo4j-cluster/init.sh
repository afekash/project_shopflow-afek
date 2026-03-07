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
echo "Waiting for cluster to form (leader election)..."
sleep 10

echo ""
echo "Seeding dataset on leader (neo4j-core1)..."
$COMPOSE exec -T neo4j-core1 cypher-shell \
  -u neo4j -p password \
  --database neo4j \
  "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;"

$COMPOSE exec -T neo4j-core1 cypher-shell \
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
