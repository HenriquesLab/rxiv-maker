<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/yaml_processor.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `yaml_processor.py`
YAML processing utilities for Rxiv-Maker. 

This module handles the extraction and parsing of YAML metadata from markdown files. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/yaml_processor.py#L35"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `fallback_processor`

```python
fallback_processor(authors)
```

Fallback function if email_encoder is not available. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/yaml_processor.py#L45"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `find_config_file`

```python
find_config_file(md_file)
```

Find the configuration file for the manuscript. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/yaml_processor.py#L61"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `extract_yaml_metadata`

```python
extract_yaml_metadata(md_file)
```

Extract yaml metadata from separate config file or from the markdown file. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/processors/yaml_processor.py#L117"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `parse_yaml_simple`

```python
parse_yaml_simple(yaml_content)
```

Simple YAML parser for basic key-value pairs. 


