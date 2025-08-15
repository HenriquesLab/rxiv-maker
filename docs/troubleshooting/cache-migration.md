# Cache Directory Migration Guide

Rxiv-Maker has migrated to using platform-standard cache directories for better system integration and to prevent cluttering project directories.

## What Changed

### Old Cache Locations
Previously, cache files were stored in local directories within your project:

**Legacy `.cache` directory:**
```
project/.cache/
├── doi_cache.json
├── bibliography_checksum_MANUSCRIPT.json
└── figure_checksums_MANUSCRIPT.json
```

**Legacy `.rxiv_cache` directory:**
```
project/.rxiv_cache/
├── doi/
│   └── doi_cache.json
├── bibliography/
│   └── bibliography_cache.json
└── figures/
    └── figure_cache.json
```

### New Cache Locations
Cache files are now stored in platform-standard locations:

**Linux**: `~/.cache/rxiv-maker/`
```
~/.cache/rxiv-maker/
├── doi/
│   └── doi_cache.json
├── bibliography/
│   └── bibliography_checksum_MANUSCRIPT.json
├── figures/
│   └── figure_checksums_MANUSCRIPT.json
└── updates/
    └── update_cache.json
```

**macOS**: `~/Library/Caches/rxiv-maker/`
```
~/Library/Caches/rxiv-maker/
├── doi/
├── bibliography/
├── figures/
└── updates/
```

**Windows**: `%LOCALAPPDATA%\rxiv-maker\Cache\`
```
C:\Users\username\AppData\Local\rxiv-maker\Cache\
├── doi\
├── bibliography\
├── figures\
└── updates\
```

## Automatic Migration

**Migration is handled automatically** when you first use rxiv-maker after the update:

1. **Detection**: Rxiv-maker checks for cache files in the old `.cache` and `.rxiv_cache` directories
2. **Migration**: Files are moved to the new platform-standard location
3. **Cleanup**: Empty legacy cache directories are removed (if empty)
4. **Logging**: Migration activities are logged for transparency

### Migration Example
```bash
# First use after update
rxiv pdf

# You'll see log messages like:
# INFO: Migrated cache: .rxiv_cache/doi -> ~/.cache/rxiv-maker/doi
# INFO: Migrated cache: .rxiv_cache/bibliography -> ~/.cache/rxiv-maker/bibliography  
# INFO: Successfully migrated .rxiv_cache to standardized location
```

## Manual Migration (If Needed)

If automatic migration fails or you want to migrate manually:

```bash
# Create new cache directories
mkdir -p ~/.cache/rxiv-maker/{doi,bibliography,figures,updates}  # Linux/macOS
# or create equivalent Windows directories

# Move cache files from .cache directory
mv .cache/doi_cache*.json ~/.cache/rxiv-maker/doi/ 2>/dev/null || true
mv .cache/bibliography_checksum*.json ~/.cache/rxiv-maker/bibliography/ 2>/dev/null || true
mv .cache/figure_checksums*.json ~/.cache/rxiv-maker/figures/ 2>/dev/null || true

# Move cache files from .rxiv_cache directory
mv .rxiv_cache/doi/* ~/.cache/rxiv-maker/doi/ 2>/dev/null || true
mv .rxiv_cache/bibliography/* ~/.cache/rxiv-maker/bibliography/ 2>/dev/null || true
mv .rxiv_cache/figures/* ~/.cache/rxiv-maker/figures/ 2>/dev/null || true

# Remove old cache directories if empty
rmdir .cache 2>/dev/null || true
rmdir .rxiv_cache/{doi,bibliography,figures} 2>/dev/null || true
rmdir .rxiv_cache 2>/dev/null || true
```

## Backward Compatibility

**Legacy cache directory support**: You can still use the old cache location by explicitly specifying it:

```python
from rxiv_maker.utils.doi_cache import DOICache

# Use legacy location
cache = DOICache(cache_dir=".cache")

# Use new standard location (default)
cache = DOICache()
```

## Benefits of New Cache Location

1. **Platform Standards**: Follows OS conventions for cache storage
2. **System Integration**: Better integration with system cleanup tools
3. **User Experience**: Cache appears in expected locations for each OS
4. **Project Cleanliness**: No cache clutter in project directories
5. **Isolation**: Cache organized by application in standard locations

## Troubleshooting

### Cache Not Migrating
If migration doesn't work automatically:

```bash
# Check if old caches exist
ls -la .cache/ .rxiv_cache/

# Check if new cache directory was created
ls -la ~/.cache/rxiv-maker/  # Linux/macOS
dir "%LOCALAPPDATA%\rxiv-maker\Cache"  # Windows

# Force recreation of cache
rm -rf ~/.cache/rxiv-maker/  # Linux/macOS
rxiv pdf  # Will recreate cache with new structure
```

### Permission Issues
If you encounter permission errors:

```bash
# Check permissions
ls -ld ~/.cache/  # Should be writable by user

# Fix permissions if needed
chmod 755 ~/.cache/
```

### Missing Cache Files
If cache files seem missing after migration:

```bash
# Check all cache locations
find ~/.cache/rxiv-maker/ -name "*.json"  # Linux/macOS

# Verify cache is working
rxiv pdf --verbose  # Will show cache activity
```

## Cache Management Commands

```bash
# View cache statistics
python -c "
from rxiv_maker.utils.doi_cache import DOICache
cache = DOICache()
print(cache.stats())
"

# Clear all caches
rm -rf ~/.cache/rxiv-maker/  # Linux/macOS
rmdir /s "%LOCALAPPDATA%\rxiv-maker\Cache"  # Windows

# Or use cleanup command
rxiv clean --cache-only
```

## Implementation Details

The migration is implemented in `src/rxiv_maker/utils/cache_utils.py` using the `platformdirs` library to ensure cross-platform compatibility. Each cache manager (DOI, bibliography, figures, updates) handles its own migration transparently.

For more information, see the [cache utilities API documentation](../api/cache_utils.py.md).
