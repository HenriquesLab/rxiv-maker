<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/file_helpers.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `file_helpers.py`
File handling utilities for Rxiv-Maker. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/file_helpers.py#L19"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `create_output_dir`

```python
create_output_dir(output_dir: str) → None
```

Create output directory if it doesn't exist. 



**Args:**
 
 - <b>`output_dir`</b>:  Path to the output directory to create. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/file_helpers.py#L32"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `find_manuscript_md`

```python
find_manuscript_md(manuscript_path: str | None = None) → Path
```

Find the main manuscript markdown file. 



**Args:**
 
 - <b>`manuscript_path`</b>:  Optional path to the manuscript directory. If not provided,  uses current directory or MANUSCRIPT_PATH environment variable. 



**Returns:**
 Path to the main manuscript file (01_MAIN.md). 



**Raises:**
 
 - <b>`FileNotFoundError`</b>:  If the manuscript file cannot be found. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/file_helpers.py#L120"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `write_manuscript_output`

```python
write_manuscript_output(
    output_dir: str,
    template_content: str,
    manuscript_name: str | None = None
) → str
```

Write the generated manuscript to the output directory. 



**Args:**
 
 - <b>`output_dir`</b>:  Directory where the manuscript will be written. 
 - <b>`template_content`</b>:  The processed LaTeX template content. 
 - <b>`manuscript_name`</b>:  Name for the manuscript file (optional, defaults to MANUSCRIPT_PATH env var). 



**Returns:**
 Path to the written manuscript file. 


