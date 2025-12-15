<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/bibliography_parser.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `bibliography_parser.py`
Bibliography file parsing utilities. 

This module provides utilities for parsing BibTeX files and extracting entry information. Used by CLI commands to provide structured bibliography data. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/bibliography_parser.py#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `parse_bib_file`

```python
parse_bib_file(bib_path: Path) → list[BibEntry]
```

Parse a BibTeX file and extract all entries. 



**Args:**
 
 - <b>`bib_path`</b>:  Path to the .bib file 



**Returns:**
 List of parsed bibliography entries 



**Raises:**
 
 - <b>`FileNotFoundError`</b>:  If the bibliography file doesn't exist 
 - <b>`ValueError`</b>:  If the file cannot be parsed 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/bibliography_parser.py#L47"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `parse_bib_content`

```python
parse_bib_content(content: str) → list[BibEntry]
```

Parse BibTeX content and extract all entries. 



**Args:**
 
 - <b>`content`</b>:  BibTeX file content 



**Returns:**
 List of parsed bibliography entries 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/bibliography_parser.py#L186"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `entry_to_dict`

```python
entry_to_dict(entry: BibEntry, include_raw: bool = False) → dict[str, Any]
```

Convert a BibEntry to a dictionary for JSON serialization. 



**Args:**
 
 - <b>`entry`</b>:  The bibliography entry 
 - <b>`include_raw`</b>:  Whether to include the raw BibTeX entry 



**Returns:**
 Dictionary representation of the entry 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/bibliography_parser.py#L204"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `format_author_list`

```python
format_author_list(author_string: str) → list[str]
```

Format author string into a list of individual authors. 



**Args:**
 
 - <b>`author_string`</b>:  The author field from a BibTeX entry (e.g., "Smith, J. and Doe, J.") 



**Returns:**
 List of author names 


---

## <kbd>class</kbd> `BibEntry`
Represents a parsed bibliography entry. 





