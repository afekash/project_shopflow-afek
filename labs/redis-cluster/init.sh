#!/usr/bin/env bash
# Initialize Redis Cluster: join 6 nodes into a cluster with 3 primaries and 3 replicas.
# Run after: make lab-redis-cluster
# Called automatically by: make redis-cluster-init

set -e

echo "Waiting for all Redis nodes to be ready..."
for node in redis-node-1 redis-node-2 redis-node-3 redis-node-4 redis-node-5 redis-node-6; do
  until docker compose -f labs/base/compose.yml -f labs/redis-cluster/compose.yml exec -T "$node" redis-cli -p 6380 ping | grep -q PONG; do
    sleep 1
  done
  echo "  $node: ready"
done

echo ""
echo "Creating cluster (3 primaries + 3 replicas)..."

# Resolve container IPs
get_ip() {
  docker compose -f labs/base/compose.yml -f labs/redis-cluster/compose.yml exec -T "$1" \
    sh -c "hostname -i | awk '{print \$1}'"
}

N1=$(get_ip redis-node-1)
N2=$(get_ip redis-node-2)
N3=$(get_ip redis-node-3)
N4=$(get_ip redis-node-4)
N5=$(get_ip redis-node-5)
N6=$(get_ip redis-node-6)

echo "  Node IPs: $N1 $N2 $N3 $N4 $N5 $N6"

docker compose -f labs/base/compose.yml -f labs/redis-cluster/compose.yml exec -T redis-node-1 \
  redis-cli -p 6380 --cluster create \
    "$N1:6380" "$N2:6380" "$N3:6380" \
    "$N4:6380" "$N5:6380" "$N6:6380" \
    --cluster-replicas 1 \
    --cluster-yes

echo ""
echo "Redis Cluster is ready."
echo "Connect from workspace: redis-py ClusterClient at redis-node-1:6380"
