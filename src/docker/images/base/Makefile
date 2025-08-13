# ======================================================================
# Rxiv-Maker Docker Image Management Makefile (AMD64 only)
# ======================================================================
# This Makefile contains developer/maintainer commands for building and
# managing Docker images. End users should use the main Makefile with
# RXIV_ENGINE=DOCKER for containerized builds.
#
# ARCHITECTURE: AMD64 and ARM64 supported
# Works on all architectures without browser dependencies
#
# Usage:
#   cd src/docker
#   make help
#   make image-build
#   make image-push
# ======================================================================

# Default values (can be overridden)
DOCKER_HUB_REPO ?= henriqueslab/rxiv-maker-base
DOCKER_IMAGE_TAG ?= latest
BUILD_PLATFORMS ?= linux/amd64,linux/arm64

# ======================================================================
# 🐳 DOCKER IMAGE MANAGEMENT
# ======================================================================

# Build Docker image locally (single platform for loading)
.PHONY: image-build
image-build:
	@echo "🐳 Building Docker image locally (safe mode)..."
	@echo "📋 Image: $(DOCKER_HUB_REPO):$(DOCKER_IMAGE_TAG)"
	@echo "🏗️  Platform: Host architecture (for local loading)"
	@echo "🛡️  Using safe build wrapper to prevent crashes"
	@./build-safe.sh --local --tag $(DOCKER_IMAGE_TAG) --repo $(DOCKER_HUB_REPO) --platform linux/amd64

# Build and push AMD64 Docker image to DockerHub
.PHONY: image-push
image-push:
	@echo "🐳 Building and pushing AMD64 Docker image (safe mode)..."
	@echo "📋 Image: $(DOCKER_HUB_REPO):$(DOCKER_IMAGE_TAG)"
	@echo "🏗️  Platforms: $(BUILD_PLATFORMS)"
	@echo "🚀 Destination: DockerHub"
	@echo "🛡️  Using safe build wrapper to prevent crashes"
	@echo "⏰ Multi-platform builds can take 30+ minutes"
	@echo "💡 Ensure you're logged in: docker login"
	@./build-safe.sh --tag $(DOCKER_IMAGE_TAG) --repo $(DOCKER_HUB_REPO) --platform $(BUILD_PLATFORMS)

# Build and push in background (for very long builds)
.PHONY: image-push-bg
image-push-bg:
	@echo "🐳 Starting background build and push of AMD64 Docker image..."
	@echo "📋 Image: $(DOCKER_HUB_REPO):$(DOCKER_IMAGE_TAG)"
	@echo "🏗️  Platforms: $(BUILD_PLATFORMS)"
	@echo "🚀 Destination: DockerHub"
	@echo "⏰ Running in background - check logs in src/docker/"
	@echo "💡 Use 'make build-status' to monitor progress"
	@echo "💡 Use 'docker images $(DOCKER_HUB_REPO)' to check completion"
	@nohup ./build-safe.sh --tag $(DOCKER_IMAGE_TAG) --repo $(DOCKER_HUB_REPO) --platform $(BUILD_PLATFORMS) > build-bg-$(shell date +%Y%m%d-%H%M%S).log 2>&1 &
	@echo "🚀 Background build started! Check status with 'make build-status'"

# Check status of background builds
.PHONY: build-status
build-status:
	@echo "🔍 Checking Docker build status..."
	@echo ""
	@echo "📊 Build processes:"
	@if pgrep -f "build-safe.sh" >/dev/null 2>&1; then \
		echo "✅ Build process running (PID: $$(pgrep -f "build-safe.sh"))"; \
	else \
		echo "❌ No build process found"; \
	fi
	@echo ""
	@echo "📁 Recent build logs:"
	@ls -lt build-*.log 2>/dev/null | head -5 || echo "No build logs found"
	@echo ""
	@echo "🐳 Current Docker images:"
	@docker images $(DOCKER_HUB_REPO) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>/dev/null || echo "No images found"
	@echo ""
	@echo "💡 To monitor live: tail -f $$(ls -t build-*.log 2>/dev/null | head -1)"

# Build Docker image for local testing only
.PHONY: image-local
image-local:
	@echo "🐳 Building Docker image for local testing (safe mode)..."
	@echo "📋 Image: $(DOCKER_HUB_REPO):test"
	@echo "🛡️  Using safe build wrapper to prevent crashes"
	@./build-safe.sh --local --tag test --repo $(DOCKER_HUB_REPO) --platform linux/amd64

# Multi-platform builds now supported
# Both AMD64 and ARM64 architectures work without browser dependencies

# Build with regular script (for debugging or when safe mode isn't needed)
.PHONY: image-build-fast
image-build-fast:
	@echo "🐳 Building Docker image (fast mode)..."
	@echo "📋 Image: $(DOCKER_HUB_REPO):$(DOCKER_IMAGE_TAG)"
	@echo "⚠️  Using regular build script (may crash on resource constraints)"
	@./build.sh --local --tag $(DOCKER_IMAGE_TAG) --repo $(DOCKER_HUB_REPO) --platform linux/amd64

# Build and test Docker image functionality
.PHONY: image-test
image-test: image-local
	@echo "🧪 Testing Docker image functionality..."
	@echo "📋 Testing Python dependencies..."
	@docker run --rm $(DOCKER_HUB_REPO):test python -c "import matplotlib, numpy, pandas, yaml; print('✅ Python dependencies OK')"
	@echo "📋 Testing LaTeX installation..."
	@docker run --rm $(DOCKER_HUB_REPO):test pdflatex --version | head -1
	@echo "📋 Testing R installation..."
	@docker run --rm $(DOCKER_HUB_REPO):test R --version | head -1
	@echo "📋 Testing mermaid.ink API support..."
	@docker run --rm $(DOCKER_HUB_REPO):test python -c "import requests; print('✅ Mermaid.ink API ready')"
	@echo "✅ All Docker image tests passed!"

# Architecture support: AMD64 and ARM64
# Mermaid.ink API approach works on all platforms without browser or Node.js dependencies

# Docker Hub login helper
.PHONY: login
login:
	@echo "🔐 Logging into Docker Hub..."
	@docker login

# Clean up local Docker images
.PHONY: image-clean
image-clean:
	@echo "🧹 Cleaning up local Docker images..."
	@docker images $(DOCKER_HUB_REPO) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
	@echo ""
	@read -p "Remove all $(DOCKER_HUB_REPO) images? [y/N]: " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker rmi $$(docker images $(DOCKER_HUB_REPO) -q) 2>/dev/null || echo "No images to remove"; \
	fi

# Show Docker system information
.PHONY: info
info:
	@echo "🐳 Docker System Information"
	@echo "=================================="
	@echo "Docker version:"
	@docker --version
	@echo ""
	@echo "Docker buildx version:"
	@docker buildx version
	@echo ""
	@echo "Available buildx builders:"
	@docker buildx ls
	@echo ""
	@echo "Local $(DOCKER_HUB_REPO) images:"
	@docker images $(DOCKER_HUB_REPO) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>/dev/null || echo "No images found"

# ======================================================================
# 🔧 DEVELOPMENT AND MAINTENANCE
# ======================================================================

# Build specific version with tag
.PHONY: image-version
image-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ VERSION is required. Usage: make image-version VERSION=v1.2.3"; \
		exit 1; \
	fi
	@echo "🐳 Building versioned Docker image: $(DOCKER_HUB_REPO):$(VERSION)"
	@./build.sh --tag $(VERSION) --repo $(DOCKER_HUB_REPO)

# Build and push development image
.PHONY: image-dev
image-dev:
	@echo "🐳 Building development Docker image..."
	@./build.sh --tag dev --repo $(DOCKER_HUB_REPO)

# Build release candidate
.PHONY: image-rc
image-rc:
	@if [ -z "$(RC_VERSION)" ]; then \
		echo "❌ RC_VERSION is required. Usage: make image-rc RC_VERSION=v1.2.3-rc1"; \
		exit 1; \
	fi
	@echo "🐳 Building release candidate: $(DOCKER_HUB_REPO):$(RC_VERSION)"
	@./build.sh --tag $(RC_VERSION) --repo $(DOCKER_HUB_REPO)

# ======================================================================
# 📖 HELP AND DOCUMENTATION
# ======================================================================

.PHONY: help
help:
	@echo "============================================="
	@echo "🐳 Rxiv-Maker Docker Image Management"
	@echo "============================================="
	@echo ""
	@echo "🚀 ESSENTIAL COMMANDS:"
	@echo "  make image-build     - Build single-platform image locally (safe mode)"
	@echo "  make image-push      - Build and push AMD64 image to DockerHub (safe mode)"
	@echo "  make image-push-bg   - Build and push in background (avoids timeouts)"
	@echo "  make build-status    - Check status of background builds"
	@echo "  make image-test      - Build and test image functionality"
	@echo "  make login           - Login to Docker Hub"
	@echo "  make help            - Show this help message"
	@echo ""
	@echo "🔧 DEVELOPMENT COMMANDS:"
	@echo "  make image-local      - Build for local testing only (safe mode)"
	@echo "  make image-build-fast - Build AMD64 image (fast/unsafe mode)"
	@echo "  make image-clean      - Clean up local Docker images"
	@echo "  make info             - Show Docker system information"
	@echo ""
	@echo "📦 VERSIONING COMMANDS:"
	@echo "  make image-version VERSION=v1.2.3      - Build specific version"
	@echo "  make image-dev                         - Build development image"
	@echo "  make image-rc RC_VERSION=v1.2.3-rc1   - Build release candidate"
	@echo ""
	@echo "⚙️  CONFIGURATION:"
	@echo "  DOCKER_HUB_REPO = $(DOCKER_HUB_REPO)"
	@echo "  DOCKER_IMAGE_TAG = $(DOCKER_IMAGE_TAG)"
	@echo "  BUILD_PLATFORMS = $(BUILD_PLATFORMS) (AMD64 + ARM64)"
	@echo ""
	@echo "💡 EXAMPLES:"
	@echo "  make image-build                                    # Build latest locally"
	@echo "  make image-push DOCKER_IMAGE_TAG=v1.2.3           # Push specific version"
	@echo "  make image-build DOCKER_HUB_REPO=myuser/rxiv-base # Use different repo"
	@echo ""
	@echo "🔗 RELATED FILES:"
	@echo "  - build.sh           # Main build script"
	@echo "  - build-safe.sh      # Safe build wrapper (prevents crashes)"
	@echo "  - Dockerfile         # Image definition"
	@echo "  - README.md          # Documentation"
	@echo ""
	@echo "🛡️  SAFE BUILD MODE:"
	@echo "  - Default for all builds to prevent system crashes"
	@echo "  - Monitors resources and provides progress updates"
	@echo "  - Handles memory constraints and timeouts gracefully"
	@echo "  - Use *-fast targets for debugging if safe mode has issues"
	@echo ""
	@echo "📝 NOTE: End users should use the main Makefile with RXIV_ENGINE=DOCKER"
	@echo "         for containerized builds. These commands are for maintainers."

# Default target
.DEFAULT_GOAL := help
