<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/utils/doi_cache.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `doi_cache.py`
DOI cache system for storing CrossRef API responses. 



---

## <kbd>class</kbd> `DOICache`
Cache system for DOI metadata from CrossRef API. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/utils/doi_cache.py#L15"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(
    cache_dir: str = '.cache',
    cache_filename: Optional[str] = None,
    manuscript_name: Optional[str] = None
)
```

Initialize DOI cache. 



**Args:**
 
 - <b>`cache_dir`</b>:  Directory to store cache files 
 - <b>`cache_filename`</b>:  Name of the cache file (if None, uses manuscript-specific naming) 
 - <b>`manuscript_name`</b>:  Name of the manuscript (used for manuscript-specific caching) 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/utils/doi_cache.py#L208"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `cleanup_expired`

```python
cleanup_expired() → int
```

Remove expired entries from cache. 



**Returns:**
  Number of entries removed 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/utils/doi_cache.py#L202"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `clear`

```python
clear() → None
```

Clear all cached entries. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/utils/doi_cache.py#L91"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get`

```python
get(doi: str) → Optional[dict[str, Any]]
```

Get cached metadata for a DOI. 



**Args:**
 
 - <b>`doi`</b>:  DOI to look up 



**Returns:**
 Cached metadata if available and not expired, None otherwise 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/utils/doi_cache.py#L167"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_resolution_status`

```python
get_resolution_status(doi: str) → Optional[dict[str, Any]]
```

Get cached resolution status for a DOI. 



**Args:**
 
 - <b>`doi`</b>:  DOI to look up 



**Returns:**
 Resolution status if available and not expired, None otherwise 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/utils/doi_cache.py#L122"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `set`

```python
set(doi: str, metadata: dict[str, Any]) → None
```

Cache metadata for a DOI. 



**Args:**
 
 - <b>`doi`</b>:  DOI to cache 
 - <b>`metadata`</b>:  Metadata to cache 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/utils/doi_cache.py#L136"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `set_resolution_status`

```python
set_resolution_status(
    doi: str,
    resolves: bool,
    error_message: Optional[str] = None
) → None
```

Cache DOI resolution status. 



**Args:**
 
 - <b>`doi`</b>:  DOI to cache status for 
 - <b>`resolves`</b>:  Whether the DOI resolves 
 - <b>`error_message`</b>:  Optional error message if resolution failed 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/utils/doi_cache.py#L232"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `stats`

```python
stats() → dict[str, Any]
```

Get cache statistics. 



**Returns:**
  Dictionary with cache statistics 


