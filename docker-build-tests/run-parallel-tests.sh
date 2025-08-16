#!/bin/bash

# Parallel Docker build performance test
# Tests all optimization strategies simultaneously

echo "Starting parallel Docker build performance tests..."
echo "This will test all 5 optimization strategies simultaneously"

# Create results directory
mkdir -p results

# Function to run a single test
run_test() {
    local strategy=$1
    local dockerfile=$2
    local tag=$3

    echo "Starting test for $strategy..."
    start_time=$(date +%s)

    # Run the build and capture output
    podman build -f "$dockerfile" -t "$tag" . \
        > "results/${strategy}-output.log" 2>&1

    exit_code=$?
    end_time=$(date +%s)
    duration=$((end_time - start_time))

    if [ $exit_code -eq 0 ]; then
        echo "✅ $strategy COMPLETED in ${duration}s"
        echo "${duration}s" > "results/${strategy}-time.txt"

        # Get image size
        size=$(podman images --format "{{.Size}}" "$tag" 2>/dev/null || echo "unknown")
        echo "$size" > "results/${strategy}-size.txt"
    else
        echo "❌ $strategy FAILED after ${duration}s"
        echo "FAILED" > "results/${strategy}-time.txt"
        echo "N/A" > "results/${strategy}-size.txt"
    fi
}

# Start all tests in parallel
echo "Launching all 5 strategies in parallel..."

run_test "strategy-1-current" "strategy-1-current.Dockerfile" "test-current" &
PID1=$!

run_test "strategy-2-ubuntu-r" "strategy-2-ubuntu-r.Dockerfile" "test-ubuntu-r" &
PID2=$!

run_test "strategy-3-multistage" "strategy-3-multistage.Dockerfile" "test-multistage" &
PID3=$!

run_test "strategy-4-parallel" "strategy-4-parallel.Dockerfile" "test-parallel" &
PID4=$!

run_test "strategy-5-minimal" "strategy-5-minimal.Dockerfile" "test-minimal" &
PID5=$!

# Wait for all tests to complete
echo "Waiting for all tests to complete..."
wait $PID1 $PID2 $PID3 $PID4 $PID5

echo ""
echo "All tests completed! Generating summary..."

# Generate results summary
echo "========================================="
echo "DOCKER BUILD PERFORMANCE TEST RESULTS"
echo "========================================="
echo ""

# Show results for each strategy
for strategy in strategy-1-current strategy-2-ubuntu-r strategy-3-multistage strategy-4-parallel strategy-5-minimal; do
    time_file="results/${strategy}-time.txt"
    size_file="results/${strategy}-size.txt"

    if [ -f "$time_file" ] && [ -f "$size_file" ]; then
        time_result=$(cat "$time_file")
        size_result=$(cat "$size_file")
        echo "📊 $strategy:"
        echo "   Build Time: $time_result"
        echo "   Image Size: $size_result"
        echo ""
    else
        echo "❌ $strategy: No results found"
        echo ""
    fi
done

# Find the fastest successful build
echo "Finding the fastest successful build..."
fastest_time=999999
fastest_strategy=""

for strategy in strategy-1-current strategy-2-ubuntu-r strategy-3-multistage strategy-4-parallel strategy-5-minimal; do
    time_file="results/${strategy}-time.txt"
    if [ -f "$time_file" ]; then
        time_result=$(cat "$time_file")
        if [[ "$time_result" =~ ^[0-9]+s$ ]]; then
            # Extract numeric value
            time_numeric=${time_result%s}
            if [ "$time_numeric" -lt "$fastest_time" ]; then
                fastest_time=$time_numeric
                fastest_strategy=$strategy
            fi
        fi
    fi
done

if [ -n "$fastest_strategy" ]; then
    echo "🏆 WINNER: $fastest_strategy (${fastest_time}s)"
    echo ""
    echo "Recommendation: Use $fastest_strategy for the main Dockerfile"
else
    echo "⚠️  No successful builds found"
fi

echo ""
echo "Check the results/ directory for detailed logs from each test."
