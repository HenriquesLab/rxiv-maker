#!/bin/bash

# Docker Build Performance Testing Script
# Tests different strategies for optimizing Docker builds with Podman

set -e

echo "🚀 Starting Docker build performance tests..."
echo "Testing on architecture: $(uname -m)"

# Create results directory
mkdir -p results
RESULTS_FILE="results/build-times-$(date +%Y%m%d-%H%M%S).csv"

# Initialize CSV file
echo "Strategy,Architecture,BuildTime(seconds),ImageSize(MB),Status,Notes" > "$RESULTS_FILE"

# Function to test a strategy
test_strategy() {
    local strategy_num="$1"
    local strategy_name="$2"
    local dockerfile="strategy-${strategy_num}-${strategy_name}.Dockerfile"
    local arch="$3"

    echo "📦 Testing Strategy ${strategy_num}: ${strategy_name} on ${arch}..."

    local start_time=$(date +%s)
    local image_tag="test-strategy-${strategy_num}-${arch}"

    # Run the build with timeout
    if timeout 3600 podman build --platform "linux/${arch}" \
        -f "$dockerfile" \
        -t "$image_tag" \
        --no-cache \
        . > "results/build-log-${strategy_num}-${arch}.log" 2>&1; then

        local end_time=$(date +%s)
        local build_time=$((end_time - start_time))

        # Get image size
        local image_size=$(podman images --format "{{.Size}}" "$image_tag" | head -1)

        echo "✅ Strategy ${strategy_num} (${arch}): ${build_time}s, Size: ${image_size}"
        echo "${strategy_name},${arch},${build_time},${image_size},SUCCESS," >> "$RESULTS_FILE"

        # Test basic functionality
        if podman run --rm "$image_tag" R --slave -e "cat('R works:', R.version.string, '\n')"; then
            echo "✅ R functionality test passed"
        else
            echo "⚠️  R functionality test failed"
            echo "${strategy_name},${arch},${build_time},${image_size},SUCCESS,R-test-failed" >> "$RESULTS_FILE"
        fi

    else
        local end_time=$(date +%s)
        local build_time=$((end_time - start_time))
        echo "❌ Strategy ${strategy_num} (${arch}): FAILED after ${build_time}s"
        echo "${strategy_name},${arch},${build_time},,FAILED,Build timeout or error" >> "$RESULTS_FILE"
    fi

    echo ""
}

# Test strategies
declare -a strategies=(
    "1:current"
    "2:ubuntu-r"
    "3:multistage"
    "4:parallel"
    "5:minimal"
)

# Test on current architecture first
CURRENT_ARCH=$(uname -m)
if [[ "$CURRENT_ARCH" == "x86_64" ]]; then
    CURRENT_ARCH="amd64"
elif [[ "$CURRENT_ARCH" == "aarch64" ]]; then
    CURRENT_ARCH="arm64"
fi

echo "Testing on current architecture: $CURRENT_ARCH"

for strategy in "${strategies[@]}"; do
    IFS=':' read -r num name <<< "$strategy"
    test_strategy "$num" "$name" "$CURRENT_ARCH"
done

# If running on Apple Silicon, also test AMD64 via emulation
if [[ "$CURRENT_ARCH" == "arm64" ]]; then
    echo "🔄 Testing AMD64 emulation..."
    for strategy in "${strategies[@]}"; do
        IFS=':' read -r num name <<< "$strategy"
        echo "Testing Strategy $num on AMD64 (emulated)..."
        test_strategy "$num" "$name" "amd64"
    done
fi

echo "📊 Build performance test completed!"
echo "Results saved to: $RESULTS_FILE"

# Display summary
echo ""
echo "📈 SUMMARY:"
echo "=========="
column -t -s',' "$RESULTS_FILE"

echo ""
echo "📁 Log files available in results/ directory"
echo "🔍 Review build logs for detailed analysis"
