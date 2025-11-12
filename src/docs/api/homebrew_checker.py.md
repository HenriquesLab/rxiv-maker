<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/homebrew_checker.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `homebrew_checker.py`
Homebrew update checker for rxiv-maker. 

Checks if a newer version is available via Homebrew. 

Note: Before upgrading with Homebrew, always run 'brew update' first to fetch the latest formulae. 

**Global Variables**
---------------
- **FORMULA_NAME**
- **FORMULA_URL**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/homebrew_checker.py#L19"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_brew_outdated`

```python
check_brew_outdated(
    package: str = 'rxiv-maker',
    timeout: int = 5
) → Optional[Tuple[str, str]]
```

Check if package is outdated using `brew outdated` command. 



**Args:**
 
 - <b>`package`</b>:  Package name to check 
 - <b>`timeout`</b>:  Command timeout in seconds 



**Returns:**
 Tuple of (current_version, latest_version) if outdated, None otherwise Returns None if brew is not installed or command fails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/homebrew_checker.py#L61"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_homebrew_update`

```python
check_homebrew_update(current_version: str) → Optional[Tuple[bool, str]]
```

Check if a Homebrew update is available. 

Checks via the brew outdated command to see if a newer version is available in the Homebrew tap. 



**Args:**
 
 - <b>`current_version`</b>:  Current installed version 



**Returns:**
 Tuple of (has_update, latest_version) if check succeeds, None on failure 


