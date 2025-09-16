#!/usr/bin/env bash
# Orchestrate local CI reproduction using the project Dockerfile.ci
# Provides targets mirroring GitHub Actions jobs so failures can be forecast locally.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE_TAG="rxiv-maker-ci:local"
PYTHON_VERSION="3.11"
ARTIFACT_DIR="${REPO_ROOT}/.ci_artifacts"
NOX_CMD="/opt/uv-venv/bin/nox"

usage(){
  cat <<'EOF'
Usage: scripts/run-ci-locally.sh <command> [-- pytest-args]

Commands (mirrors CI jobs):
  build-image          Build/update the CI image
  fast                 Run fast tests (lint + unit subset)
  fast-logs            Run fast tests & capture logs under .ci_artifacts
  integration          Run integration tests
  build-validation     Run build packaging validation
  coverage             Run full test suite with coverage (enforces threshold)
  container-pdf        Run pdf nox session (container-tests subset)
  security             Run security scans
  docs                 Run docs generation
  full                 Run fast + integration + build + coverage sequentially
  matrix               Run fast tests across Python 3.11,3.12,3.13 (best-effort)
  shell                Start interactive shell inside the CI container
  clean                Remove local image and dangling containers

Examples:
  scripts/run-ci-locally.sh build-image
  scripts/run-ci-locally.sh fast -- -k executor
  scripts/run-ci-locally.sh coverage
  scripts/run-ci-locally.sh shell
  scripts/run-ci-locally.sh fast-logs
  scripts/run-ci-locally.sh matrix
EOF
}

if [[ $# -lt 1 ]]; then
  usage; exit 1; fi

COMMAND=$1; shift || true

build_image(){
  echo "🛠  Building CI image (${IMAGE_TAG})..."
  docker build --build-arg PYTHON_VERSION=${PYTHON_VERSION} -t ${IMAGE_TAG} -f ci/Dockerfile.ci .
  echo "✅ Image built"
}

run_in_container(){
  local run_cmd=$1; shift
  # Mount repository, keep ephemeral venv & nox caches inside container to mimic CI (no reuse across runs unless image reused)
  docker run --rm -t \
    -e FORCE_COLOR=1 -e UV_SYSTEM_PYTHON=1 -e PYTHONIOENCODING=utf-8 -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 -e CI=1 -e GITHUB_ACTIONS=1 \
    -v "${REPO_ROOT}:/workspace" -w /workspace \
    ${IMAGE_TAG} bash -lc "${run_cmd}"
}

ensure_image(){
  if ! docker image inspect ${IMAGE_TAG} > /dev/null 2>&1; then
    build_image
  fi
}

timestamp(){ date +%Y%m%d-%H%M%S; }

capture_logs(){
  local name=$1; shift
  mkdir -p "${ARTIFACT_DIR}" || true
  local ts=$(timestamp)
  local log_file="${ARTIFACT_DIR}/${ts}_${name}.log"
  echo "📝 Capturing logs → ${log_file}" >&2
  run_in_container "$*" | tee "${log_file}"
  echo "✅ Logs stored at ${log_file}" >&2
}

matrix_fast(){
  local versions=(3.11 3.12 3.13)
  mkdir -p "${ARTIFACT_DIR}" || true
  for v in "${versions[@]}"; do
    local tag="${IMAGE_TAG}-${v}"
    echo "🛠  Building image for Python ${v}";
    docker build --build-arg PYTHON_VERSION=${v} -t ${tag} -f ci/Dockerfile.ci . || echo "(System package for ${v} may not exist; continuing with base image)"
    echo "🚀 Fast tests for Python ${v}";
    local ts=$(timestamp)
    local log_file="${ARTIFACT_DIR}/${ts}_fast_py${v}.log"
    docker run --rm -t \
      -e FORCE_COLOR=1 -e UV_SYSTEM_PYTHON=1 -e PYTHONIOENCODING=utf-8 -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 -e CI=1 -e GITHUB_ACTIONS=1 \
      -v "${REPO_ROOT}:/workspace" -w /workspace \
      ${tag} bash -lc "uv run nox -s \"test(test_type='fast')\"" | tee "${log_file}" || true
    echo "📄 Log: ${log_file}";
  done
  echo "✅ Matrix fast tests complete (see ${ARTIFACT_DIR})"
}

case "${COMMAND}" in
  build-image)
    build_image ;;
  fast)
    ensure_image
    echo "🚀 Running fast tests (lint + unit subset)";
  run_in_container "${NOX_CMD} -s lint && ${NOX_CMD} -s \"test(test_type='fast')\" $*" ;;
  fast-logs)
    ensure_image
    echo "🚀 Running fast tests with log capture";
  capture_logs fast "${NOX_CMD} -s lint && ${NOX_CMD} -s \"test(test_type='fast')\" $*" ;;
  integration)
    ensure_image
    echo "🔗 Running integration tests";
  run_in_container "${NOX_CMD} -s \"test(test_type='integration')\" $*" ;;
  build-validation)
    ensure_image
    echo "📦 Running build validation";
  run_in_container "${NOX_CMD} -s build" ;;
  coverage)
    ensure_image
    echo "📊 Running full test suite with coverage";
  run_in_container "${NOX_CMD} -s \"test(test_type='full')\" $*" ;;
  container-pdf)
    ensure_image
    echo "🖨  Running pdf session in container";
  run_in_container "${NOX_CMD} -s pdf" ;;
  security)
    ensure_image
    echo "🔒 Running security scans";
  run_in_container "${NOX_CMD} -s security" ;;
  docs)
    ensure_image
    echo "📚 Generating docs";
  run_in_container "${NOX_CMD} -s docs" ;;
  full)
    ensure_image
    set -e
  run_in_container "${NOX_CMD} -s lint" || exit 1
  run_in_container "${NOX_CMD} -s \"test(test_type='fast')\"" || exit 1
  run_in_container "${NOX_CMD} -s \"test(test_type='integration')\"" || exit 1
  run_in_container "${NOX_CMD} -s build" || exit 1
  run_in_container "${NOX_CMD} -s \"test(test_type='full')\"" || exit 1
    echo "✅ Full local CI sequence passed" ;;
  matrix)
    matrix_fast ;;
  shell)
    ensure_image
    echo "🐚 Opening interactive shell (type 'nox -l' to list sessions)";
    docker run --rm -it -e FORCE_COLOR=1 -e UV_SYSTEM_PYTHON=1 -e PYTHONIOENCODING=utf-8 -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 -e CI=1 -e GITHUB_ACTIONS=1 -v "${REPO_ROOT}:/workspace" -w /workspace ${IMAGE_TAG} bash ;;
  clean)
    echo "🧹 Cleaning image ${IMAGE_TAG}"; docker image rm ${IMAGE_TAG} 2>/dev/null || true; docker image prune -f ;;
  *)
    echo "❌ Unknown command: ${COMMAND}"; usage; exit 1 ;;
 esac
