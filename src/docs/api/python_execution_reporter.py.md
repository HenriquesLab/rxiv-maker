<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `python_execution_reporter.py`
Python execution reporting utility for rxiv-maker. 

This module provides centralized reporting of Python code execution during manuscript build process, including code blocks executed, outputs generated, and any errors encountered. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L290"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_python_execution_reporter`

```python
get_python_execution_reporter() → PythonExecutionReporter
```

Get or create the global Python execution reporter. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L298"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `reset_python_execution_reporter`

```python
reset_python_execution_reporter() → None
```

Reset the global Python execution reporter for a new build. 


---

## <kbd>class</kbd> `PythonExecutionEntry`
Represents a single Python execution event. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L13"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(
    entry_type: str,
    line_number: int,
    execution_time: float,
    file_path: str = 'manuscript',
    output: str = '',
    error_message: str = ''
)
```

Initialize execution entry. 





---

## <kbd>class</kbd> `PythonExecutionReporter`
Centralized reporting system for Python execution events during manuscript build. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L34"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__()
```

Initialize the reporter. 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L99"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `add_entry`

```python
add_entry(
    operation_type: str,
    line_number: int,
    execution_time: float,
    file_path: str = 'manuscript',
    output: str = '',
    error: str = ''
) → None
```

Add a general execution entry. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L275"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `display_report`

```python
display_report(verbose: bool = False) → None
```

Display the Python execution report. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L222"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `format_errors_for_display`

```python
format_errors_for_display() → str
```

Format execution errors for display. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L195"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `format_outputs_for_display`

```python
format_outputs_for_display() → str
```

Format execution outputs for display. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L163"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `format_summary_for_display`

```python
format_summary_for_display() → str
```

Format summary statistics for display. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L254"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `format_verbose_report`

```python
format_verbose_report() → str
```

Format a comprehensive report for verbose output. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L155"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_entries_with_output`

```python
get_entries_with_output() → List[PythonExecutionEntry]
```

Get all entries that have output. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L159"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_error_entries`

```python
get_error_entries() → List[PythonExecutionEntry]
```

Get all entries that have errors. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L241"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_execution_summary`

```python
get_execution_summary() → dict
```

Get execution summary compatible with build manager expectations. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L120"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_summary_statistics`

```python
get_summary_statistics() → Dict[str, Any]
```

Get summary statistics of Python execution. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L237"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `has_python_activity`

```python
has_python_activity() → bool
```

Check if any Python activity was recorded. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L39"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `reset`

```python
reset() → None
```

Reset the reporter for a new build. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L85"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `track_error`

```python
track_error(
    error_message: str,
    code_snippet: str,
    line_number: int,
    file_path: str = 'manuscript'
) → None
```

Track execution errors during manuscript processing. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L44"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `track_exec_block`

```python
track_exec_block(
    code: str,
    output: str,
    line_number: int,
    file_path: str = 'manuscript',
    execution_time: float = 0.0
) → None
```

Track execution of a Python code block. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L72"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `track_get_variable`

```python
track_get_variable(
    variable_name: str,
    variable_value: str,
    line_number: int,
    file_path: str = 'manuscript'
) → None
```

Track variable access during manuscript processing. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/python_execution_reporter.py#L58"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `track_inline_execution`

```python
track_inline_execution(
    code: str,
    output: str,
    line_number: int,
    file_path: str = 'manuscript',
    execution_time: float = 0.0
) → None
```

Track execution of inline Python code (for variable substitution). 


