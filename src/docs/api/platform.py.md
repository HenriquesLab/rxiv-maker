<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `platform.py`
Platform detection and compatibility utilities for Rxiv-Maker. 

This module provides cross-platform utilities for detecting the operating system and handling platform-specific operations like path management and command execution. 

**Global Variables**
---------------
- **platform_detector**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L356"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_platform`

```python
get_platform() → str
```

Get the current platform name. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L361"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_platform_normalized`

```python
get_platform_normalized() → str
```

Get normalized platform name for cross-platform compatibility. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L366"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_python_command`

```python
get_python_command() → str
```

Get the Python command to use. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L371"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `is_windows`

```python
is_windows() → bool
```

Check if running on Windows. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L376"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `is_unix_like`

```python
is_unix_like() → bool
```

Check if running on Unix-like system. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L381"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `run_platform_command`

```python
run_platform_command(cmd: str | list[str], **kwargs) → CompletedProcess
```

Run a command with platform-appropriate settings. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L386"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `is_in_venv`

```python
is_in_venv() → bool
```

Check if running in a virtual environment. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L391"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `is_in_conda_env`

```python
is_in_conda_env() → bool
```

Check if running in a conda/mamba environment. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L396"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_conda_env_name`

```python
get_conda_env_name() → str | None
```

Get the name of the current conda/mamba environment. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L401"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_conda_python_path`

```python
get_conda_python_path() → str | None
```

Get the conda/mamba environment Python path. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L406"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_conda_executable`

```python
get_conda_executable() → str | None
```

Get the conda or mamba executable to use. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L411"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `safe_print`

```python
safe_print(
    message: str,
    success_symbol: str = '✅',
    fallback_symbol: str = '[OK]'
) → None
```

Print a message with cross-platform compatible symbols. 



**Args:**
 
 - <b>`message`</b>:  The message to print 
 - <b>`success_symbol`</b>:  Unicode symbol to use on capable terminals 
 - <b>`fallback_symbol`</b>:  ASCII fallback symbol 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L435"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `safe_console_print`

```python
safe_console_print(
    console,
    message: str,
    style: str | None = None,
    **kwargs
) → None
```

Print a message using Rich console with cross-platform Unicode fallback. 



**Args:**
 
 - <b>`console`</b>:  Rich console instance 
 - <b>`message`</b>:  The message to print 
 - <b>`style`</b>:  Rich style to apply 
 - <b>`**kwargs`</b>:  Additional arguments to pass to console.print 


---

## <kbd>class</kbd> `PlatformDetector`
Detect and manage platform-specific operations. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L21"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__()
```

Initialize platform detector. 


---

#### <kbd>property</kbd> platform

Get the current platform name. 

---

#### <kbd>property</kbd> python_cmd

Get the Python command to use. 



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L219"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `check_command_exists`

```python
check_command_exists(command: str) → bool
```

Check if a command exists on the system. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L324"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `copy_file`

```python
copy_file(src: Path, dst: Path) → bool
```

Copy a file with error handling. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L159"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_conda_env_name`

```python
get_conda_env_name() → str | None
```

Get the name of the current conda/mamba environment. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L186"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_conda_executable`

```python
get_conda_executable() → str | None
```

Get the conda or mamba executable to use. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L165"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_conda_prefix`

```python
get_conda_prefix() → Path | None
```

Get the prefix path of the current conda/mamba environment. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L170"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_conda_python_path`

```python
get_conda_python_path() → str | None
```

Get the conda/mamba environment Python path. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L223"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_env_file_content`

```python
get_env_file_content(env_file: Path = PosixPath('.env')) → dict
```

Read environment file content if it exists. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L101"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_null_device`

```python
get_null_device() → str
```

Get the null device path for the current platform. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L97"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_path_separator`

```python
get_path_separator() → str
```

Get the path separator for the current platform. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L37"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_platform_normalized`

```python
get_platform_normalized() → str
```

Get normalized platform name for cross-platform compatibility. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L123"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_venv_activate_path`

```python
get_venv_activate_path() → str | None
```

Get the virtual environment activation script path. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L105"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_venv_python_path`

```python
get_venv_python_path() → str | None
```

Get the virtual environment Python path. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L241"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `install_uv`

```python
install_uv() → bool
```

Install uv package manager for the current platform. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L195"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `is_conda_forge_available`

```python
is_conda_forge_available() → bool
```

Check if conda-forge channel is configured. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L150"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `is_in_conda_env`

```python
is_in_conda_env() → bool
```

Check if running in a conda/mamba environment. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L141"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `is_in_venv`

```python
is_in_venv() → bool
```

Check if running in a virtual environment. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L89"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `is_linux`

```python
is_linux() → bool
```

Check if running on Linux. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L85"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `is_macos`

```python
is_macos() → bool
```

Check if running on macOS. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L93"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `is_unix_like`

```python
is_unix_like() → bool
```

Check if running on Unix-like system (macOS or Linux). 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `is_windows`

```python
is_windows() → bool
```

Check if running on Windows. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L335"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `make_executable`

```python
make_executable(path: Path) → bool
```

Make a file executable (Unix-like systems only). 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L312"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `remove_directory`

```python
remove_directory(path: Path) → bool
```

Remove a directory with platform-appropriate method. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/platform.py#L209"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `run_command`

```python
run_command(
    cmd: str | list[str],
    shell: bool = False,
    **kwargs
) → CompletedProcess
```

Run a command with platform-appropriate settings. 



**Args:**
 
 - <b>`cmd`</b>:  Command to run - use list format for security, string only when shell=True 
 - <b>`shell`</b>:  Whether to use shell (default: False for security) 
 - <b>`**kwargs`</b>:  Additional arguments to pass to subprocess.run 


