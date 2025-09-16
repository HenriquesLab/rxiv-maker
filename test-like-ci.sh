#!/bin/bash

# Script to test locally using the same environment as CI

set -e

print_usage() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  fast         Run fast unit tests (same as CI)"
    echo "  specific     Run the currently failing test"
    echo "  shell        Open interactive shell in CI environment"
    echo "  build        Build the CI Docker image"
    echo "  clean        Clean up Docker resources"
    echo ""
    echo "Examples:"
    echo "  $0 fast                    # Run all fast tests"
    echo "  $0 specific                # Run failing test"
    echo "  $0 shell                   # Interactive debugging"
}

case "$1" in
    "build")
        echo "🔨 Building CI environment Docker image..."
        docker-compose -f docker-compose.ci.yml build ci-test
        echo "✅ CI environment built successfully"
        ;;

    "fast")
        echo "🧪 Running fast unit tests (same as CI)..."
        docker-compose -f docker-compose.ci.yml run --rm ci-test-run
        ;;

    "specific")
        echo "🎯 Running specific failing test..."
        docker-compose -f docker-compose.ci.yml run --rm ci-test-specific
        ;;

    "shell")
        echo "🐚 Opening interactive shell in CI environment..."
        echo "Inside the container, you can run:"
        echo "  pytest tests/unit/ -m 'unit and not ci_exclude' --maxfail=3 --tb=short -x"
        echo "  python -m pytest tests/unit/test_python_executor.py -v"
        docker-compose -f docker-compose.ci.yml run --rm ci-test
        ;;

    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker-compose -f docker-compose.ci.yml down --volumes --remove-orphans
        docker image prune -f
        echo "✅ Cleanup completed"
        ;;

    "help"|"-h"|"--help")
        print_usage
        ;;

    *)
        if [ -z "$1" ]; then
            echo "❌ No option provided"
        else
            echo "❌ Unknown option: $1"
        fi
        echo ""
        print_usage
        exit 1
        ;;
esac
