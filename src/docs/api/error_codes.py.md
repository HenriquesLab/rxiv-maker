<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/error_codes.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `error_codes.py`
Centralized error codes for rxiv-maker. 

**Global Variables**
---------------
- **TYPE_CHECKING**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/core/error_codes.py#L299"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `create_validation_error`

```python
create_validation_error(
    error_code: 'ErrorCode',
    message: 'str | None' = None,
    file_path: 'str | None' = None,
    line_number: 'int | None' = None,
    context: 'str | None' = None,
    suggestion: 'str | None' = None
) → ValidationError
```

Create a ValidationError with structured error code. 


---

## <kbd>class</kbd> `ErrorCategory`
Error categories for organizational purposes. 





---

## <kbd>class</kbd> `ErrorCode`
Comprehensive error codes for rxiv-maker. 





