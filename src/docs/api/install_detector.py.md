<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/install_detector.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `install_detector.py`
Installation method detection for rxiv-maker. 

Detects how rxiv-maker was installed (Homebrew, pipx, uv, pip, etc.) to provide appropriate upgrade instructions. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/install_detector.py#L15"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `detect_install_method`

```python
detect_install_method() → Literal['homebrew', 'pipx', 'uv', 'pip-user', 'pip', 'dev', 'unknown']
```

Detect how rxiv-maker was installed. 



**Returns:**
 
 - <b>`Installation method`</b>:  homebrew, pipx, uv, pip-user, pip, dev, or unknown 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/install_detector.py#L84"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_upgrade_command`

```python
get_upgrade_command(
    install_method: Literal['homebrew', 'pipx', 'uv', 'pip-user', 'pip', 'dev', 'unknown']
) → str
```

Get the appropriate upgrade command for the installation method. 



**Args:**
 
 - <b>`install_method`</b>:  The detected installation method 



**Returns:**
 Upgrade command string 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/install_detector.py#L106"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_friendly_install_name`

```python
get_friendly_install_name(
    install_method: Literal['homebrew', 'pipx', 'uv', 'pip-user', 'pip', 'dev', 'unknown']
) → str
```

Get a user-friendly name for the installation method. 



**Args:**
 
 - <b>`install_method`</b>:  The detected installation method 



**Returns:**
 Friendly name string 


