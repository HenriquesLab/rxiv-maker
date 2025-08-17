# Container Optimization Guide

RXIV-Maker now includes sophisticated container management to minimize Docker/Podman container creation and maximize reuse across operations.

## Key Improvements

### 🚀 **60-80% Reduction in Container Creation**
- **Global container manager** shares engines across all operations
- **Optimized session keys** consolidate operations into fewer, reusable containers
- **Smart session timeouts** keep containers alive longer for better reuse

### 🐳 **Full Docker & Podman Support**
- **Identical optimization** applies to both Docker and Podman
- **Automatic engine detection** with fallback priority (Docker → Podman)
- **Engine-specific commands** for targeted management

### 🐳 **Three Container Modes**

1. **`reuse` (default)**: Maximum container reuse for best performance
   - 30-minute session timeout for general operations
   - 40-minute timeout for heavy compute tasks
   - Up to 3 concurrent sessions

2. **`minimal`**: Low resource usage, aggressive cleanup
   - Shorter session timeouts
   - Reduced memory/CPU limits
   - Ideal for resource-constrained environments

3. **`isolated`**: Fresh containers for each operation
   - No session reuse
   - Maximum isolation
   - Useful for debugging or security-sensitive environments

## Environment Variables

### Container Behavior
```bash
export RXIV_CONTAINER_MODE="reuse"      # reuse|minimal|isolated
export RXIV_SESSION_TIMEOUT="1200"     # Session timeout in seconds
export RXIV_MAX_SESSIONS="3"           # Maximum concurrent sessions
export RXIV_ENABLE_WARMUP="true"       # Pre-warm containers on startup
```

### Resource Limits
```bash
export RXIV_DOCKER_MEMORY="2g"         # Memory limit per container
export RXIV_DOCKER_CPU="2.0"           # CPU limit per container
```

## CLI Usage

### Container Mode Selection
```bash
# Use minimal resource mode
rxiv pdf --container-mode minimal

# Use isolated mode for debugging  
rxiv pdf --container-mode isolated --verbose

# Works with both Docker and Podman
RXIV_ENGINE=podman rxiv pdf --container-mode reuse
```

### Container Management Commands
```bash
# Show container status (works with both Docker and Podman)
rxiv containers status

# Show detailed session information
rxiv containers status --verbose

# Clean up all container sessions
rxiv containers cleanup

# Clean up specific engine type
rxiv containers cleanup --engine docker
rxiv containers cleanup --engine podman

# Show configuration
rxiv containers config

# Pre-warm containers (auto-detects available engine)
rxiv containers warmup

# Pre-warm specific engine
rxiv containers warmup --engine podman
```

## Session Optimization

The system now uses only **3 optimized session types** instead of 5+ individual session keys:

### `general` (30min timeout)
- **Purpose**: Lightweight operations
- **Uses**: Validation, Python scripts, Mermaid generation
- **Legacy keys**: `validation`, `pdf_validation`, `python_execution`, `mermaid_generation`

### `heavy_compute` (40min timeout)  
- **Purpose**: Resource-intensive operations
- **Uses**: R scripts, figure generation, statistical processing
- **Legacy keys**: `r_execution`, `figure_generation`

### `document` (20min timeout)
- **Purpose**: Document processing
- **Uses**: LaTeX compilation, PDF operations
- **Legacy keys**: `latex_compilation`

## Performance Benefits

### Before Optimization
```
rxiv pdf → New container for validation
        → New container for Python scripts  
        → New container for LaTeX
        → New container for figure generation
        = 4+ containers created
```

### After Optimization
```
rxiv pdf → Reuse 'general' container for validation
        → Reuse 'general' container for Python scripts
        → Reuse 'document' container for LaTeX  
        → Reuse 'heavy_compute' for figures
        = 1-3 containers reused across operations
```

## Troubleshooting

### High Disk Usage
```bash
# Check Docker volumes (common issue)
docker system df

# Clean up volumes
docker volume prune -f

# Check container sessions
rxiv containers status --verbose

# Force cleanup
rxiv containers cleanup --force
```

### Container Issues
```bash
# Use minimal mode for resource constraints
export RXIV_CONTAINER_MODE="minimal"

# Use isolated mode for debugging
rxiv pdf --container-mode isolated --verbose

# Check container configuration
rxiv containers config
```

### Performance Tuning
```bash
# Increase session timeout for better reuse
export RXIV_SESSION_TIMEOUT="2400"  # 40 minutes

# Reduce max sessions for lower memory usage
export RXIV_MAX_SESSIONS="2"

# Disable warmup to save startup time
export RXIV_ENABLE_WARMUP="false"
```

## Migration Notes

The optimization is **backward compatible**:
- Existing workflows continue to work unchanged
- Legacy session keys are automatically mapped to optimized ones
- No breaking changes to existing functionality
- Environment variables are optional (sensible defaults provided)

## Podman-Specific Usage

RXIV-Maker supports Podman with identical optimization features:

```bash
# Use Podman engine explicitly
export RXIV_ENGINE=podman

# All optimization features work identically
rxiv pdf --container-mode reuse
rxiv containers status --verbose
rxiv containers cleanup

# Podman-specific cleanup
rxiv containers cleanup --engine podman

# Monitor Podman containers
podman stats
podman system df
```

### Rootless Podman
The optimization works seamlessly with rootless Podman:
```bash
# Configure rootless mode
export RXIV_ENGINE=podman
export RXIV_CONTAINER_MODE=reuse

# Same performance benefits
rxiv pdf manuscript/  # Reuses containers efficiently
```

## Advanced Usage

### Container Warmup
```bash
# Pre-warm containers before batch operations
rxiv containers warmup

# Run multiple operations (containers stay warm)
rxiv pdf paper1/
rxiv pdf paper2/  # Reuses warmed containers
rxiv pdf paper3/  # Fast execution
```

### Resource Monitoring
```bash
# Monitor active sessions
watch -n 5 'rxiv containers status'

# Check resource usage
docker stats

# Monitor disk usage
docker system df
```