#!/bin/bash

# Refresh tokens
aws sso login --profile jonny-dev

# Copy to project directory 
mkdir -p project-aws/sso/cache
cp ~/.aws/sso/cache/* project-aws/sso/cache/

docker-compose -f docker-compose-dev.yaml up --build frontend backend