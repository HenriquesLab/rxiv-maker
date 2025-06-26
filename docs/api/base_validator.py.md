<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/validators/base_validator.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `base_validator.py`
Base validator class and common validation types. 



---

## <kbd>class</kbd> `BaseValidator`
Abstract base class for all validators. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/validators/base_validator.py#L100"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(manuscript_path: str)
```

Initialize validator with manuscript path. 



**Args:**
 
 - <b>`manuscript_path`</b>:  Path to the manuscript directory 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/validators/base_validator.py#L109"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate`

```python
validate() → ValidationResult
```

Perform validation and return results. 



**Returns:**
  ValidationResult with any issues found 


---

## <kbd>class</kbd> `ValidationError`
Represents a single validation issue. 





---

## <kbd>class</kbd> `ValidationLevel`
Validation result severity levels. 





---

## <kbd>class</kbd> `ValidationResult`
Results from a validation operation. 


---

#### <kbd>property</kbd> error_count

Count of error-level issues. 

---

#### <kbd>property</kbd> has_errors

Check if there are any error-level issues. 

---

#### <kbd>property</kbd> has_warnings

Check if there are any warning-level issues. 

---

#### <kbd>property</kbd> warning_count

Count of warning-level issues. 



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/validators/base_validator.py#L92"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_errors_by_level`

```python
get_errors_by_level(level: ValidationLevel) → list[ValidationError]
```

Get all errors of a specific level. 


