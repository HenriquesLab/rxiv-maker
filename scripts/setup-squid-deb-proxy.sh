#!/bin/bash
# ======================================================================
# squid-deb-proxy Setup for Docker Build Acceleration
# ======================================================================
# This script sets up a local squid-deb-proxy to cache apt packages
# across Docker builds, providing massive speedup (reported as the
# biggest performance improvement in Docker build acceleration).
#
# Based on research from:
# https://gist.github.com/reegnz/990d0b01b5f5e8670f78257875d8daa8
#
# Usage:
#   ./scripts/setup-squid-deb-proxy.sh
#
# Then build with:
#   docker build --network squid \
#     --build-arg http_proxy=http://squid-deb-proxy:8000 \
#     -t henriqueslab/rxiv-maker-base:latest .
#
# ======================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up squid-deb-proxy for Docker build acceleration${NC}"

# Create Dockerfile for squid-deb-proxy
cat > Dockerfile.squid-deb-proxy << 'EOF'
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install squid-deb-proxy
RUN apt-get update && apt-get install -y --no-install-recommends \
    squid-deb-proxy \
    && rm -rf /var/lib/apt/lists/*

# Create data directory
RUN mkdir -p /data

# Expose squid port
EXPOSE 8000

# Start squid-deb-proxy
CMD ["/usr/bin/squid-deb-proxy", "-N", "-d", "1"]
EOF

echo -e "${YELLOW}📦 Building squid-deb-proxy Docker image...${NC}"
docker build -t rxiv-maker/squid-deb-proxy -f Dockerfile.squid-deb-proxy .

echo -e "${YELLOW}🔗 Creating Docker network 'squid'...${NC}"
# Create network if it doesn't exist
if ! docker network ls | grep -q "squid"; then
    docker network create squid
    echo -e "${GREEN}✅ Created Docker network 'squid'${NC}"
else
    echo -e "${GREEN}✅ Docker network 'squid' already exists${NC}"
fi

echo -e "${YELLOW}💾 Creating volume for cache persistence...${NC}"
# Create volume if it doesn't exist
if ! docker volume ls | grep -q "squid-deb-proxy"; then
    docker volume create squid-deb-proxy
    echo -e "${GREEN}✅ Created volume 'squid-deb-proxy'${NC}"
else
    echo -e "${GREEN}✅ Volume 'squid-deb-proxy' already exists${NC}"
fi

echo -e "${YELLOW}🏃 Starting squid-deb-proxy container...${NC}"
# Stop existing container if running
if docker ps -q -f name=squid-deb-proxy | grep -q .; then
    echo -e "${YELLOW}⏹️  Stopping existing squid-deb-proxy container...${NC}"
    docker stop squid-deb-proxy
    docker rm squid-deb-proxy
fi

# Start the proxy container
docker run -d \
    --name squid-deb-proxy \
    --network squid \
    --volume squid-deb-proxy:/data \
    --restart unless-stopped \
    rxiv-maker/squid-deb-proxy

echo -e "${GREEN}✅ squid-deb-proxy is running!${NC}"
echo ""
echo -e "${BLUE}📋 Usage Instructions:${NC}"
echo -e "  To build with proxy acceleration:"
echo -e "  ${YELLOW}docker build --network squid \\${NC}"
echo -e "  ${YELLOW}    --build-arg http_proxy=http://squid-deb-proxy:8000 \\${NC}"
echo -e "  ${YELLOW}    -t henriqueslab/rxiv-maker-base:latest .${NC}"
echo ""
echo -e "  To stop the proxy:"
echo -e "  ${YELLOW}docker stop squid-deb-proxy${NC}"
echo ""
echo -e "  To view proxy logs:"
echo -e "  ${YELLOW}docker logs -f squid-deb-proxy${NC}"

# Cleanup temporary Dockerfile
rm -f Dockerfile.squid-deb-proxy

echo -e "${GREEN}🎉 squid-deb-proxy setup complete!${NC}"
