#!/bin/bash

export APOLLO_ELV2_LICENSE=accept

npx @apollo/federation-subgraph-compatibility docker \
 --compose ./examples/docker-compose.yml \
 --path /graphql \
 --schema ./products.graphql \
 --debug
