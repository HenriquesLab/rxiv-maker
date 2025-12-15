<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/author_name_formatter.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `author_name_formatter.py`
Author name parsing and formatting utilities. 

This module provides functionality to parse, format, and transform author names between different bibliographic citation formats. 

Supported formats: 
- lastname_initials: "Smith, J.A." 
- lastname_firstname: "Smith, John A." 
- firstname_lastname: "John A. Smith" 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/author_name_formatter.py#L16"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `extract_initials`

```python
extract_initials(given_name: str) → str
```

Extract initials from a given name. 



**Args:**
 
 - <b>`given_name`</b>:  Given name(s), which may include first and middle names 



**Returns:**
 Formatted initials with periods 



**Examples:**
 ``` extract_initials("John Alan")```
    'J.A.'
    >>> extract_initials("J. A.")
    'J.A.'
    >>> extract_initials("Jean-Paul")
    'J.-P.'
    >>> extract_initials("John")
    'J.'



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/author_name_formatter.py#L75"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `parse_author_name`

```python
parse_author_name(name_str: str) → Dict[str, str]
```

Parse an author name into components. 

Handles both "LastName, FirstName MiddleName" and "FirstName MiddleName LastName" formats. 



**Args:**
 
 - <b>`name_str`</b>:  Author name string to parse 



**Returns:**
 
 - <b>`Dictionary with keys`</b>:  first, middle, last, suffix, von Empty strings for missing components 



**Examples:**
 ``` parse_author_name("Smith, John A.")```
    {'first': 'John', 'middle': 'A.', 'last': 'Smith', 'suffix': '', 'von': ''}
    >>> parse_author_name("von Neumann, John")
    {'first': 'John', 'middle': '', 'last': 'von Neumann', 'suffix': '', 'von': 'von'}
    >>> parse_author_name("Martin, James Jr.")
    {'first': 'James', 'middle': '', 'last': 'Martin', 'suffix': 'Jr.', 'von': ''}
    >>> parse_author_name("John A. Smith")
    {'first': 'John', 'middle': 'A.', 'last': 'Smith', 'suffix': '', 'von': ''}



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/author_name_formatter.py#L197"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `format_author_name`

```python
format_author_name(author_parts: Dict[str, str], format_type: str) → str
```

Format an author name according to the specified format. 



**Args:**
 
 - <b>`author_parts`</b>:  Dictionary with author name components (from parse_author_name) 
 - <b>`format_type`</b>:  One of "lastname_initials", "lastname_firstname", "firstname_lastname" 



**Returns:**
 Formatted author name string 



**Examples:**
 ``` parts = {'first': 'John', 'middle': 'A.', 'last': 'Smith', 'suffix': '', 'von': ''}```
    >>> format_author_name(parts, "lastname_initials")
    'Smith, J.A.'
    >>> format_author_name(parts, "lastname_firstname")
    'Smith, John A.'
    >>> format_author_name(parts, "firstname_lastname")
    'John A. Smith'



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/rxiv_maker/utils/author_name_formatter.py#L271"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `format_author_list`

```python
format_author_list(authors_str: str, format_type: str) → str
```

Format a list of authors separated by 'and'. 

Note: Caller should clean LaTeX commands from authors_str before calling this function. 



**Args:**
 
 - <b>`authors_str`</b>:  String of authors separated by " and " (should be LaTeX-cleaned) 
 - <b>`format_type`</b>:  One of "lastname_initials", "lastname_firstname", "firstname_lastname" 



**Returns:**
 Formatted author list joined by " and " 



**Examples:**
 ``` format_author_list("Smith, John and Jones, Mary A.", "lastname_initials")```
    'Smith, J. and Jones, M.A.'
    >>> format_author_list("Smith, John A. and Jones, Mary", "firstname_lastname")
    'John A. Smith and Mary Jones'



