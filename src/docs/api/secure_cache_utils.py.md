<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/secure_cache_utils.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `secure_cache_utils.py`
Secure cache utilities for rxiv-maker with comprehensive security hardening. 

This module provides secure cache directory management with protection against: 
- Path traversal attacks 
- TOCTOU race conditions 
- Symlink attacks 
- Disk space exhaustion 
- Permission escalation 

**Global Variables**
---------------
- **MAX_CACHE_SIZE_MB**
- **MAX_FILE_SIZE_MB**
- **CACHE_PERMISSIONS**
- **FILE_PERMISSIONS**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/secure_cache_utils.py#L179"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_secure_cache_dir`

```python
get_secure_cache_dir(subfolder: Optional[str] = None) → Path
```

Get the standardized cache directory with security validation. 



**Args:**
 
 - <b>`subfolder`</b>:  Optional subfolder within the cache directory 



**Returns:**
 Path to the cache directory 



**Raises:**
 
 - <b>`SecurityError`</b>:  If path validation fails 
 - <b>`PermissionError`</b>:  If cache directory cannot be created or accessed 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/secure_cache_utils.py#L179"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_secure_cache_dir`

```python
get_secure_cache_dir(subfolder: Optional[str] = None) → Path
```

Get the standardized cache directory with security validation. 



**Args:**
 
 - <b>`subfolder`</b>:  Optional subfolder within the cache directory 



**Returns:**
 Path to the cache directory 



**Raises:**
 
 - <b>`SecurityError`</b>:  If path validation fails 
 - <b>`PermissionError`</b>:  If cache directory cannot be created or accessed 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/secure_cache_utils.py#L232"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `secure_migrate_cache_file`

```python
secure_migrate_cache_file(
    legacy_path: Path,
    new_path: Path,
    force: bool = False
) → bool
```

Securely migrate a cache file with comprehensive validation. 



**Args:**
 
 - <b>`legacy_path`</b>:  Path to the legacy cache file 
 - <b>`new_path`</b>:  Path to the new cache file location 
 - <b>`force`</b>:  If True, overwrite existing file at new location 



**Returns:**
 True if migration was performed, False otherwise 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/secure_cache_utils.py#L232"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `secure_migrate_cache_file`

```python
secure_migrate_cache_file(
    legacy_path: Path,
    new_path: Path,
    force: bool = False
) → bool
```

Securely migrate a cache file with comprehensive validation. 



**Args:**
 
 - <b>`legacy_path`</b>:  Path to the legacy cache file 
 - <b>`new_path`</b>:  Path to the new cache file location 
 - <b>`force`</b>:  If True, overwrite existing file at new location 



**Returns:**
 True if migration was performed, False otherwise 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/secure_cache_utils.py#L320"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `secure_migrate_cache_directory`

```python
secure_migrate_cache_directory(
    source_dir: Optional[Path] = None,
    force: bool = False,
    max_size_mb: int = 1000
) → bool
```

Securely migrate cache directory with comprehensive validation. 



**Args:**
 
 - <b>`source_dir`</b>:  Source directory containing cache 
 - <b>`force`</b>:  If True, overwrite existing files 
 - <b>`max_size_mb`</b>:  Maximum total size to migrate in MB 



**Returns:**
 True if migration was performed, False otherwise 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/secure_cache_utils.py#L320"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `secure_migrate_cache_directory`

```python
secure_migrate_cache_directory(
    source_dir: Optional[Path] = None,
    force: bool = False,
    max_size_mb: int = 1000
) → bool
```

Securely migrate cache directory with comprehensive validation. 



**Args:**
 
 - <b>`source_dir`</b>:  Source directory containing cache 
 - <b>`force`</b>:  If True, overwrite existing files 
 - <b>`max_size_mb`</b>:  Maximum total size to migrate in MB 



**Returns:**
 True if migration was performed, False otherwise 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/secure_cache_utils.py#L455"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `validate_cache_security`

```python
validate_cache_security() → dict[str, Any]
```

Validate cache system security configuration. 



**Returns:**
  Dictionary with security validation results 


---

## <kbd>class</kbd> `SecurityError`
Raised when a security violation is detected. 





