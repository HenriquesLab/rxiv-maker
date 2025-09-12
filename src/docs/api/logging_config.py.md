<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logging_config.py`
Centralized logging configuration for rxiv-maker. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L168"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_logger`

```python
get_logger() → RxivLogger
```

Get the global logger instance. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L173"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `debug`

```python
debug(message: str) → None
```

Log debug message. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L178"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `info`

```python
info(message: str) → None
```

Log info message. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L183"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `success`

```python
success(message: str) → None
```

Log success message. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L188"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `warning`

```python
warning(message: str) → None
```

Log warning message. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L193"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `error`

```python
error(message: str) → None
```

Log error message. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L198"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `critical`

```python
critical(message: str) → None
```

Log critical message. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L203"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `docker_info`

```python
docker_info(message: str) → None
```

Log Docker-related info. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L208"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `tip`

```python
tip(message: str) → None
```

Log helpful tip. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L213"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `set_quiet`

```python
set_quiet(quiet: bool = True) → None
```

Enable/disable quiet mode. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L218"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `set_debug`

```python
set_debug(debug_mode: bool = True) → None
```

Enable/disable debug mode. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L226"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `set_log_directory`

```python
set_log_directory(log_dir: Path) → None
```

Set the directory where log files should be created. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L231"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_log_file_path`

```python
get_log_file_path() → Path | None
```

Get the current log file path. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L236"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cleanup`

```python
cleanup() → None
```

Clean up logging resources. 


---

## <kbd>class</kbd> `RxivLogger`
Centralized logging configuration for rxiv-maker with Rich support. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L26"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__() → None
```

Initialize the singleton instance only once. 


---

#### <kbd>property</kbd> console

Get the Rich console instance. 



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L146"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `cleanup`

```python
cleanup() → None
```

Clean up resources, especially file handlers for Windows compatibility. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L127"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `critical`

```python
critical(message: str) → None
```

Log critical message. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L107"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `debug`

```python
debug(message: str) → None
```

Log debug message. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L131"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `docker_info`

```python
docker_info(message: str) → None
```

Log Docker-related info. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L123"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `error`

```python
error(message: str) → None
```

Log error message. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L79"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_log_file_path`

```python
get_log_file_path() → Path | None
```

Get the current log file path. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L111"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `info`

```python
info(message: str) → None
```

Log info message. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L83"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `set_level`

```python
set_level(level: str) → None
```

Set logging level. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L61"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `set_log_directory`

```python
set_log_directory(log_dir: Path) → None
```

Set the directory where log files should be created. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L100"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `set_quiet`

```python
set_quiet(quiet: bool = True) → None
```

Enable/disable quiet mode (only errors and warnings). 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L115"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `success`

```python
success(message: str) → None
```

Log success message. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L135"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `tip`

```python
tip(message: str) → None
```

Log helpful tip. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/logging_config.py#L119"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `warning`

```python
warning(message: str) → None
```

Log warning message. 


