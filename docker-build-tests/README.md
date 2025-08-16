# Docker Build Optimization Tests

This directory contains test strategies for optimizing Docker builds, particularly for ARM64/multiarch scenarios.

## Test Strategies

1. **strategy-1-current.Dockerfile** - Current approach (baseline)
2. **strategy-2-ubuntu-r.Dockerfile** - Use Ubuntu's R packages instead of CRAN
3. **strategy-3-multistage.Dockerfile** - Multi-stage build with R pre-compilation
4. **strategy-4-parallel.Dockerfile** - Parallel package installation
5. **strategy-5-minimal.Dockerfile** - Minimal R packages, skip graphics

## Testing Commands

```bash
# Test with Podman (multiarch)
podman build --platform linux/arm64,linux/amd64 -f strategy-X.Dockerfile -t test-strategy-X .

# Test with timing
time podman build --platform linux/arm64 -f strategy-X.Dockerfile -t test-strategy-X-arm64 .
time podman build --platform linux/amd64 -f strategy-X.Dockerfile -t test-strategy-X-amd64 .

# Test build size
podman images | grep test-strategy
```

## Benchmark Results

| Strategy | ARM64 Time | AMD64 Time | Image Size | Notes |
|----------|------------|------------|------------|-------|
| Current  | TBD        | TBD        | TBD        | Baseline |
| Ubuntu-R | TBD        | TBD        | TBD        | Ubuntu packages |
| Multi-stage | TBD     | TBD        | TBD        | Pre-compilation |
| Parallel | TBD        | TBD        | TBD        | Parallel install |
| Minimal  | TBD        | TBD        | TBD        | Minimal packages |
