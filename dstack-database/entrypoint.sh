#!/bin/bash

# Replace environment variables in configuration
sed -i "s/#{NODE_IP}/${NODE_IP}/g" /etc/patroni/patroni.yml
sed -i "s/#{ETCD_HOSTS}/${ETCD_HOSTS}/g" /etc/patroni/patroni.yml
sed -i "s/#{REPLICATION_PASSWORD}/${REPLICATION_PASSWORD}/g" /etc/patroni/patroni.yml
sed -i "s/#{POSTGRES_PASSWORD}/${POSTGRES_PASSWORD}/g" /etc/patroni/patroni.yml

# Start Patroni
exec patroni /etc/patroni/patroni.yml