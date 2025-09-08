<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/verification.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `verification.py`
Installation verification utilities. 

**Global Variables**
---------------
- **DependencyChecker**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/verification.py#L18"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_installation`

```python
verify_installation(verbose: bool = False) → dict[str, bool]
```

Verify that all required components are installed and working. 



**Args:**
 
 - <b>`verbose`</b>:  Enable verbose output 



**Returns:**
 Dictionary mapping component names to installation status 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/verification.py#L52"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_system_dependencies`

```python
check_system_dependencies() → list[str]
```

Check system dependencies and return list of missing components. 



**Returns:**
  List of missing dependency names 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/verification.py#L152"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `diagnose_installation`

```python
diagnose_installation() → dict[str, dict[str, Any]]
```

Perform detailed diagnosis of installation issues. 



**Returns:**
  Dictionary with detailed diagnostic information 


