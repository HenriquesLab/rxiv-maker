<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/commands/validate.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `validate.py`
Unified validation command for rxiv-maker manuscripts. 

This command provides a comprehensive validation system that checks: 
- Manuscript structure and required files 
- Citation syntax and bibliography consistency 
- Cross-reference validity (figures, tables, equations) 
- Figure file existence and attributes 
- Mathematical expression syntax 
- Special Markdown syntax elements 
- LaTeX compilation errors (if available) 

The command produces user-friendly output with clear error messages, suggestions for fixes, and optional detailed statistics. 

**Global Variables**
---------------
- **VALIDATORS_AVAILABLE**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/commands/validate.py#L283"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main()
```

Main entry point for unified validation command. 


---

## <kbd>class</kbd> `UnifiedValidator`
Unified validation system for rxiv-maker manuscripts. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/commands/validate.py#L44"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(
    manuscript_path: str,
    verbose: bool = False,
    include_info: bool = False,
    check_latex: bool = True
)
```

Initialize unified validator. 



**Args:**
 
 - <b>`manuscript_path`</b>:  Path to manuscript directory 
 - <b>`verbose`</b>:  Show detailed output 
 - <b>`include_info`</b>:  Include informational messages 
 - <b>`check_latex`</b>:  Parse LaTeX compilation errors 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/commands/validate.py#L141"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `print_detailed_report`

```python
print_detailed_report() → None
```

Print detailed validation report. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/commands/validate.py#L258"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `print_summary`

```python
print_summary() → None
```

Print brief validation summary. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/commands/validate.py#L67"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate_all`

```python
validate_all() → bool
```

Run all available validators. 


