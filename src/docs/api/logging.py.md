<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/logging.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logging.py`
Logging utilities for installation process. 



---

## <kbd>class</kbd> `InstallLogger`
Logger for installation process with file and console output. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/logging.py#L14"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(log_file: Path | None = None, verbose: bool = False)
```

Initialize the logger. 



**Args:**
 
 - <b>`log_file`</b>:  Path to log file (auto-generated if None) 
 - <b>`verbose`</b>:  Enable verbose console output 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/logging.py#L65"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `debug`

```python
debug(message: str)
```

Log debug message. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/logging.py#L60"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `error`

```python
error(message: str)
```

Log error message. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/logging.py#L74"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_log_file`

```python
get_log_file() → Path
```

Get the log file path. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/logging.py#L51"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `info`

```python
info(message: str)
```

Log info message. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/logging.py#L69"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `success`

```python
success(message: str)
```

Log success message. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/logging.py#L55"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `warning`

```python
warning(message: str)
```

Log warning message. 


