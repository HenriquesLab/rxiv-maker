<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/engines/operations/validate.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/engines/operations/validate.py#L361"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `validate_manuscript`

```python
validate_manuscript(
    manuscript_path: str,
    verbose: bool = False,
    include_info: bool = False,
    check_latex: bool = True,
    enable_doi_validation: bool | None = None,
    detailed: bool = False
) → bool
```

Validate manuscript with comprehensive checks. 



**Args:**
 
 - <b>`manuscript_path`</b>:  Path to the manuscript directory 
 - <b>`verbose`</b>:  Show detailed validation progress and statistics 
 - <b>`include_info`</b>:  Include informational messages in output 
 - <b>`check_latex`</b>:  Skip LaTeX compilation error parsing 
 - <b>`enable_doi_validation`</b>:  Enable/disable DOI validation. If None, reads from config 
 - <b>`detailed`</b>:  Show detailed error report with context and suggestions 



**Returns:**
 True if validation passed, False otherwise 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/engines/operations/validate.py#L411"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main()
```

Main entry point for validate command. 


---

## <kbd>class</kbd> `UnifiedValidator`
Unified validation system for rxiv-maker manuscripts. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/engines/operations/validate.py#L55"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(
    manuscript_path: str,
    verbose: bool = False,
    include_info: bool = False,
    check_latex: bool = True,
    enable_doi_validation: bool = True
)
```

Initialize unified validator. 



**Args:**
 
 - <b>`manuscript_path`</b>:  Path to manuscript directory 
 - <b>`verbose`</b>:  Show detailed output 
 - <b>`include_info`</b>:  Include informational messages 
 - <b>`check_latex`</b>:  Parse LaTeX compilation errors 
 - <b>`enable_doi_validation`</b>:  Enable DOI validation against CrossRef API 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/engines/operations/validate.py#L168"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `print_detailed_report`

```python
print_detailed_report() → None
```

Print detailed validation report. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/engines/operations/validate.py#L300"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `print_summary`

```python
print_summary() → None
```

Print brief validation summary. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/engines/operations/validate.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate_all`

```python
validate_all() → bool
```

Run all available validators. 


