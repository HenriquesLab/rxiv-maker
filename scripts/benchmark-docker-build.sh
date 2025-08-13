#!/bin/bash
# ======================================================================
# Docker Build Performance Benchmarking Suite
# ======================================================================
# This script measures Docker build performance with and without
# acceleration optimizations to quantify the speedup achieved.
#
# Tests performed:
# 1. Baseline build (no optimizations)
# 2. BuildKit cache mounts only
# 3. devxy.io R repository only
# 4. All optimizations combined
# 5. squid-deb-proxy (if available)
#
# ======================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BENCHMARK_DIR="/tmp/rxiv-maker-benchmark-$(date +%s)"
DOCKERFILE_BASE="src/docker/images/base/Dockerfile"
NUM_RUNS="${NUM_RUNS:-1}"

echo -e "${BLUE}🏁 Docker Build Performance Benchmark${NC}"
echo -e "${BLUE}====================================${NC}"
echo -e "Runs per test: ${YELLOW}${NUM_RUNS}${NC}"
echo -e "Results will be saved to: ${YELLOW}${BENCHMARK_DIR}${NC}"
echo ""

# Create benchmark directory
mkdir -p "${BENCHMARK_DIR}"

# Results array
declare -a RESULTS=()

# Function to run a timed build
run_build_test() {
    local test_name="$1"
    local dockerfile="$2"
    local build_args="$3"
    local image_tag="rxiv-maker-benchmark:${test_name}"

    echo -e "${BLUE}🧪 Running test: ${test_name}${NC}"
    echo -e "   Dockerfile: ${dockerfile}"
    echo -e "   Args: ${build_args}"

    # Clean up any existing image
    docker rmi "${image_tag}" 2>/dev/null || true

    local total_time=0
    local successful_runs=0

    for ((i=1; i<=NUM_RUNS; i++)); do
        echo -e "${YELLOW}   Run ${i}/${NUM_RUNS}...${NC}"

        # Clear all BuildKit cache for fair comparison
        docker buildx prune -f >/dev/null 2>&1 || true

        local start_time
        start_time=$(date +%s.%3N)

        # Run the build
        local build_command="docker build ${build_args} -t ${image_tag} -f ${dockerfile} ."
        if eval ${build_command} > "${BENCHMARK_DIR}/${test_name}-run${i}.log" 2>&1; then
            local end_time
            end_time=$(date +%s.%3N)
            local run_time
            run_time=$(echo "${end_time} - ${start_time}" | bc)

            total_time=$(echo "${total_time} + ${run_time}" | bc)
            ((successful_runs++))

            echo -e "${GREEN}   ✅ Run ${i}: ${run_time}s${NC}"
        else
            echo -e "${RED}   ❌ Run ${i}: FAILED${NC}"
            echo -e "      Check log: ${BENCHMARK_DIR}/${test_name}-run${i}.log"
        fi
    done

    if [[ $successful_runs -gt 0 ]]; then
        local avg_time
        avg_time=$(echo "scale=3; ${total_time} / ${successful_runs}" | bc)
        RESULTS+=("${test_name}:${avg_time}")
        echo -e "${GREEN}📊 Average time for ${test_name}: ${avg_time}s (${successful_runs}/${NUM_RUNS} successful)${NC}"
    else
        RESULTS+=("${test_name}:FAILED")
        echo -e "${RED}💥 All runs failed for ${test_name}${NC}"
    fi

    echo ""
}

# Create test Dockerfiles
echo -e "${YELLOW}📝 Creating test Dockerfiles...${NC}"

# 1. Baseline Dockerfile (no optimizations)
cat > "${BENCHMARK_DIR}/Dockerfile.baseline" << 'EOF'
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Basic system packages (no cache mounts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget build-essential r-base python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install a few R packages (no binary repos)
RUN R -e "install.packages(c('ggplot2', 'dplyr'), repos='https://cran.rstudio.com/')"

# Install a few Python packages
RUN pip3 install numpy pandas matplotlib

CMD ["/bin/bash"]
EOF

# 2. BuildKit cache mounts only
cat > "${BENCHMARK_DIR}/Dockerfile.cache-mounts" << 'EOF'
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Basic system packages WITH cache mounts
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl wget build-essential r-base python3 python3-pip

# Install R packages with cache
RUN --mount=type=cache,target=/root/.cache/R,sharing=locked \
    R -e "install.packages(c('ggplot2', 'dplyr'), repos='https://cran.rstudio.com/')"

# Install Python packages with cache
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip3 install numpy pandas matplotlib

CMD ["/bin/bash"]
EOF

# 3. devxy.io R repository only
cat > "${BENCHMARK_DIR}/Dockerfile.devxy" << 'EOF'
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Basic system packages (no cache mounts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget build-essential r-base python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Configure R with devxy.io binary repository
RUN echo 'options(repos = c("https://cran.devxy.io/amd64/jammy/latest", "https://cran.rstudio.com/"))' >> /usr/lib/R/etc/Rprofile.site

# Install R packages from binary repo
RUN R -e "install.packages(c('ggplot2', 'dplyr'))"

# Install Python packages
RUN pip3 install numpy pandas matplotlib

CMD ["/bin/bash"]
EOF

# 4. All optimizations combined
cp "${DOCKERFILE_BASE}" "${BENCHMARK_DIR}/Dockerfile.optimized"

echo -e "${GREEN}✅ Test Dockerfiles created${NC}"
echo ""

# Run benchmarks
echo -e "${BLUE}🏃 Running benchmarks...${NC}"

# Test 1: Baseline
run_build_test "baseline" "${BENCHMARK_DIR}/Dockerfile.baseline" ""

# Test 2: BuildKit cache mounts only
if command -v docker buildx >/dev/null 2>&1; then
    run_build_test "cache-mounts" "${BENCHMARK_DIR}/Dockerfile.cache-mounts" ""
else
    echo -e "${YELLOW}⚠️  Skipping cache-mounts test - BuildKit not available${NC}"
fi

# Test 3: devxy.io R repository only
run_build_test "devxy-repo" "${BENCHMARK_DIR}/Dockerfile.devxy" ""

# Test 4: All optimizations
run_build_test "optimized" "${BENCHMARK_DIR}/Dockerfile.optimized" ""

# Test 5: With squid-deb-proxy (if available)
if docker ps | grep -q "squid-deb-proxy"; then
    run_build_test "with-proxy" "${BENCHMARK_DIR}/Dockerfile.optimized" "--network squid --build-arg http_proxy=http://squid-deb-proxy:8000"
else
    echo -e "${YELLOW}⚠️  Skipping proxy test - squid-deb-proxy not running${NC}"
fi

# Generate report
echo -e "${BLUE}📊 BENCHMARK RESULTS${NC}"
echo -e "${BLUE}===================${NC}"

# Save results to file
REPORT_FILE="${BENCHMARK_DIR}/benchmark-results.txt"
echo "Docker Build Performance Benchmark Results" > "${REPORT_FILE}"
echo "Generated on: $(date)" >> "${REPORT_FILE}"
echo "Host: $(hostname)" >> "${REPORT_FILE}"
echo "Docker version: $(docker --version)" >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

baseline_time=""
for result in "${RESULTS[@]}"; do
    IFS=':' read -r name time <<< "$result"
    echo "${name}: ${time}s" >> "${REPORT_FILE}"

    if [[ "$name" == "baseline" && "$time" != "FAILED" ]]; then
        baseline_time="$time"
    fi

    if [[ "$time" == "FAILED" ]]; then
        echo -e "${RED}${name}: FAILED${NC}"
    else
        if [[ -n "$baseline_time" && "$baseline_time" != "FAILED" && "$name" != "baseline" ]]; then
            speedup=$(echo "scale=2; (${baseline_time} - ${time}) / ${baseline_time} * 100" | bc)
            echo -e "${GREEN}${name}: ${time}s (${speedup}% faster)${NC}"
            echo "${name}: ${time}s (${speedup}% faster)" >> "${REPORT_FILE}"
        else
            echo -e "${GREEN}${name}: ${time}s${NC}"
        fi
    fi
done

echo ""
echo -e "${BLUE}📄 Detailed report saved to: ${YELLOW}${REPORT_FILE}${NC}"
echo -e "${BLUE}📁 Build logs available in: ${YELLOW}${BENCHMARK_DIR}${NC}"

# Summary
if [[ -n "$baseline_time" && "$baseline_time" != "FAILED" ]]; then
    echo ""
    echo -e "${BLUE}🎯 SUMMARY${NC}"
    echo -e "${BLUE}=========${NC}"
    echo -e "Baseline build time: ${YELLOW}${baseline_time}s${NC}"

    best_time="$baseline_time"
    best_name="baseline"
    for result in "${RESULTS[@]}"; do
        IFS=':' read -r name time <<< "$result"
        if [[ "$time" != "FAILED" && $(echo "$time < $best_time" | bc -l) -eq 1 ]]; then
            best_time="$time"
            best_name="$name"
        fi
    done

    if [[ "$best_name" != "baseline" ]]; then
        improvement=$(echo "scale=1; (${baseline_time} - ${best_time}) / ${baseline_time} * 100" | bc)
        echo -e "Best configuration: ${GREEN}${best_name}${NC}"
        echo -e "Best time: ${GREEN}${best_time}s${NC}"
        echo -e "Overall improvement: ${GREEN}${improvement}%${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🏁 Benchmark complete!${NC}"
