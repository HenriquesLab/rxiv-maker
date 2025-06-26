<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `validate_manuscript.py`
Enhanced Manuscript Validation Script for Rxiv-Maker. 

This script provides comprehensive validation for manuscript directories, including structure, content, syntax, and LaTeX compilation error analysis. 

The validator checks for: 
- Required files (config, main content, bibliography) 
- Required directories (figures) 
- Configuration file validity 
- Basic content structure 
- Citation syntax and bibliography references 
- Cross-reference consistency (figures, tables, equations) 
- Figure file existence and syntax 
- Mathematical expression validity 
- Special Markdown syntax elements 
- LaTeX compilation errors (if log file exists) 

**Global Variables**
---------------
- **current_dir**
- **parent_dir**
- **ENHANCED_VALIDATION_AVAILABLE**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L523"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main()
```

Main entry point for the manuscript validator. 


---

## <kbd>class</kbd> `ManuscriptValidator`
Validates manuscript structure and requirements for Rxiv-Maker. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(
    manuscript_path: Path,
    skip_enhanced: bool = False,
    show_stats: bool = False
)
```

Initialize validator with manuscript directory path. 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L258"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `check_figure_references`

```python
check_figure_references() → None
```

Check if referenced figures exist in the FIGURES directory. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L428"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `print_summary`

```python
print_summary() → None
```

Print validation summary. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L290"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `run_enhanced_validation`

```python
run_enhanced_validation() → bool
```

Run enhanced semantic validation using new validators. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L399"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate`

```python
validate() → bool
```

Run all validation checks. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L192"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate_bibliography`

```python
validate_bibliography() → bool
```

Basic validation of the bibliography file. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L155"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate_config_file`

```python
validate_config_file() → bool
```

Validate the configuration YAML file. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L96"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate_directory_structure`

```python
validate_directory_structure() → bool
```

Validate that the manuscript directory exists and is accessible. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L218"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate_main_content`

```python
validate_main_content() → bool
```

Basic validation of the main manuscript file. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L125"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate_optional_files`

```python
validate_optional_files() → None
```

Check for optional files and warn if missing. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L136"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate_required_directories`

```python
validate_required_directories() → bool
```

Check for required directories. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/scripts/validate_manuscript.py#L111"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `validate_required_files`

```python
validate_required_files() → bool
```

Check for required files in the manuscript directory. 


