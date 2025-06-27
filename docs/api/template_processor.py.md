<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/template_processor.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `template_processor.py`
Template processing utilities for Rxiv-Maker. 

This module handles template content generation and replacement operations. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/template_processor.py#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_template_path`

```python
get_template_path()
```

Get the path to the template file. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/template_processor.py#L28"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `find_supplementary_md`

```python
find_supplementary_md()
```

Find supplementary information file in the manuscript directory. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/template_processor.py#L41"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `generate_supplementary_cover_page`

```python
generate_supplementary_cover_page(yaml_metadata)
```

Generate LaTeX code for the supplementary information cover page. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/template_processor.py#L89"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `generate_supplementary_tex`

```python
generate_supplementary_tex(output_dir, yaml_metadata=None)
```

Generate Supplementary.tex file from supplementary markdown. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/template_processor.py#L242"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `generate_keywords`

```python
generate_keywords(yaml_metadata)
```

Generate LaTeX keywords section from YAML metadata. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/template_processor.py#L259"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `generate_bibliography`

```python
generate_bibliography(yaml_metadata)
```

Generate LaTeX bibliography section from YAML metadata. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/template_processor.py#L270"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `process_template_replacements`

```python
process_template_replacements(template_content, yaml_metadata, article_md)
```

Process all template replacements with metadata and content. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/template_processor.py#L525"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `parse_supplementary_sections`

```python
parse_supplementary_sections(content)
```

Parse supplementary markdown content into separate sections. 

Separates content based on level 2 headers: 
- ## Supplementary Tables 
- ## Supplementary Notes 
- ## Supplementary Figures 



**Returns:**
 
 - <b>`dict`</b>:  Dictionary with 'tables', 'notes', and 'figures' keys 


