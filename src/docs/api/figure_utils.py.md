<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/manuscript_utils/figure_utils.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `figure_utils.py`
Figure generation utilities for manuscript Python code. 

This module provides functions that can be called from manuscript Python blocks to generate figures programmatically. These functions wrap the core figure generation functionality and make it available for use in executable manuscripts. 

**Global Variables**
---------------
- **FigureGenerator**
- **EnvironmentManager**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/manuscript_utils/figure_utils.py#L27"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `convert_mermaid`

```python
convert_mermaid(
    input_file: Union[str, Path],
    output_format: str = 'png',
    output_dir: Optional[str, Path] = None,
    **kwargs
) → List[Path]
```

Convert a Mermaid diagram file to the specified format. 



**Args:**
 
 - <b>`input_file`</b>:  Path to the .mmd file to convert 
 - <b>`output_format`</b>:  Output format ('png', 'svg', 'pdf', 'eps') 
 - <b>`output_dir`</b>:  Output directory (defaults to FIGURES subdirectory) 
 - <b>`**kwargs`</b>:  Additional arguments passed to the figure generator 



**Returns:**
 List of generated file paths 



**Raises:**
 
 - <b>`FigureGenerationError`</b>:  If generation fails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/manuscript_utils/figure_utils.py#L47"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `convert_python_figure`

```python
convert_python_figure(
    input_file: Union[str, Path],
    output_format: str = 'png',
    output_dir: Optional[str, Path] = None,
    **kwargs
) → List[Path]
```

Convert a Python figure script to the specified format. 



**Args:**
 
 - <b>`input_file`</b>:  Path to the .py file to execute 
 - <b>`output_format`</b>:  Output format ('png', 'svg', 'pdf', 'eps') 
 - <b>`output_dir`</b>:  Output directory (defaults to FIGURES subdirectory) 
 - <b>`**kwargs`</b>:  Additional arguments passed to the figure generator 



**Returns:**
 List of generated file paths 



**Raises:**
 
 - <b>`FigureGenerationError`</b>:  If generation fails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/manuscript_utils/figure_utils.py#L67"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `convert_r_figure`

```python
convert_r_figure(
    input_file: Union[str, Path],
    output_format: str = 'png',
    output_dir: Optional[str, Path] = None,
    **kwargs
) → List[Path]
```

Convert an R script to the specified format. 



**Args:**
 
 - <b>`input_file`</b>:  Path to the .R file to execute 
 - <b>`output_format`</b>:  Output format ('png', 'svg', 'pdf', 'eps') 
 - <b>`output_dir`</b>:  Output directory (defaults to FIGURES subdirectory) 
 - <b>`**kwargs`</b>:  Additional arguments passed to the figure generator 



**Returns:**
 List of generated file paths 



**Raises:**
 
 - <b>`FigureGenerationError`</b>:  If generation fails or R not available 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/manuscript_utils/figure_utils.py#L93"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `convert_figures_bulk`

```python
convert_figures_bulk(
    pattern: str,
    output_format: str = 'png',
    output_dir: Optional[str, Path] = None,
    figure_types: Optional[List[str]] = None,
    **kwargs
) → List[Path]
```

Convert multiple figure files matching a pattern. 



**Args:**
 
 - <b>`pattern`</b>:  Glob pattern to match files (e.g., '*.mmd', 'Figure_*.py') 
 - <b>`output_format`</b>:  Output format ('png', 'svg', 'pdf', 'eps') 
 - <b>`output_dir`</b>:  Output directory (defaults to FIGURES directory) 
 - <b>`figure_types`</b>:  List of figure types to process (['mermaid', 'python', 'r']) 
 - <b>`**kwargs`</b>:  Additional arguments passed to the figure generator 



**Returns:**
 List of all generated file paths 



**Raises:**
 
 - <b>`FigureGenerationError`</b>:  If generation fails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/manuscript_utils/figure_utils.py#L265"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `list_available_figures`

```python
list_available_figures(figures_dir: Optional[str, Path] = None) → dict
```

List all available figure source files. 



**Args:**
 
 - <b>`figures_dir`</b>:  Directory to search (defaults to detected FIGURES directory) 



**Returns:**
 Dictionary with figure types as keys and lists of files as values 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/manuscript_utils/figure_utils.py#L289"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_figure_info`

```python
get_figure_info(input_file: Union[str, Path]) → dict
```

Get information about a figure file. 



**Args:**
 
 - <b>`input_file`</b>:  Path to the figure source file 



**Returns:**
 Dictionary with file information 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/manuscript_utils/figure_utils.py#L326"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `clean_figure_outputs`

```python
clean_figure_outputs(
    input_file: Optional[str, Path] = None,
    output_dir: Optional[str, Path] = None
) → int
```

Clean generated figure outputs. 



**Args:**
 
 - <b>`input_file`</b>:  Specific figure to clean (cleans all if None) 
 - <b>`output_dir`</b>:  Output directory to clean 



**Returns:**
 Number of files removed 


---

## <kbd>class</kbd> `FigureGenerationError`
Exception raised during figure generation. 





