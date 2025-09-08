<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/cache_utils.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `cache_utils.py`
Cache utilities for rxiv-maker. 

Provides manuscript-local cache directory management using .rxiv_cache. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/cache_utils.py#L9"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `find_manuscript_directory`

```python
find_manuscript_directory(
    start_path: Path | None = None,
    max_depth: int = 5
) → Path | None
```

Find the manuscript directory by locating 00_CONFIG.yml file. 

Walks up the directory tree from the starting path to find a directory containing 00_CONFIG.yml, which indicates a manuscript root. 



**Args:**
 
 - <b>`start_path`</b>:  Path to start searching from (defaults to current directory) 
 - <b>`max_depth`</b>:  Maximum depth to search up the directory tree 



**Returns:**
 Path to manuscript directory if found, None otherwise 



**Examples:**
 ``` find_manuscript_directory()```
    PosixPath('/path/to/manuscript')  # if 00_CONFIG.yml found

    >>> find_manuscript_directory(Path('/path/to/manuscript/subdir'))
    PosixPath('/path/to/manuscript')  # walks up to find config



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/cache_utils.py#L46"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_manuscript_cache_dir`

```python
get_manuscript_cache_dir(
    subfolder: str | None = None,
    manuscript_dir: Path | None = None
) → Path
```

Get the manuscript-local cache directory (.rxiv_cache in manuscript directory). 



**Args:**
 
 - <b>`subfolder`</b>:  Optional subfolder within the cache directory 
 - <b>`manuscript_dir`</b>:  Manuscript directory (if None, auto-detected) 



**Returns:**
 Path to manuscript-local cache directory 



**Raises:**
 
 - <b>`RuntimeError`</b>:  If no manuscript directory is found 



**Examples:**
 ``` get_manuscript_cache_dir()```
    PosixPath('/path/to/manuscript/.rxiv_cache')

    >>> get_manuscript_cache_dir("doi")
    PosixPath('/path/to/manuscript/.rxiv_cache/doi')



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/cache_utils.py#L89"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_manuscript_name`

```python
get_manuscript_name(manuscript_dir: Path | None = None) → str | None
```

Get the manuscript name from the manuscript directory. 



**Args:**
 
 - <b>`manuscript_dir`</b>:  Manuscript directory (if None, auto-detected) 



**Returns:**
 Manuscript directory name if found, None otherwise 



**Examples:**
 ``` get_manuscript_name()```
    'MANUSCRIPT'  # if in /path/to/MANUSCRIPT directory



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/cache/cache_utils.py#L111"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `is_in_manuscript_directory`

```python
is_in_manuscript_directory() → bool
```

Check if current working directory is within a manuscript directory. 



**Returns:**
  True if in a manuscript directory, False otherwise 



**Examples:**
 ``` is_in_manuscript_directory()```
     True  # if 00_CONFIG.yml found in current dir or parent dirs



