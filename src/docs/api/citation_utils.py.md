<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/citation_utils.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `citation_utils.py`
Citation handling utilities for Rxiv-Maker. 

**Global Variables**
---------------
- **CANONICAL_RXIV_CITATION**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/citation_utils.py#L20"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `extract_existing_citation`

```python
extract_existing_citation(bib_content: str) → Optional[Tuple[str, int, int]]
```

Extract existing rxiv-maker citation from bibliography content. 



**Args:**
 
 - <b>`bib_content`</b>:  The bibliography file content 



**Returns:**
 Tuple of (citation_content, start_index, end_index) if found, None otherwise 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/citation_utils.py#L38"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `is_citation_outdated`

```python
is_citation_outdated(existing_citation: str) → bool
```

Check if the existing citation is outdated compared to canonical version. 



**Args:**
 
 - <b>`existing_citation`</b>:  The existing citation content 



**Returns:**
 True if citation needs updating, False if it's current 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/citation_utils.py#L61"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `inject_rxiv_citation`

```python
inject_rxiv_citation(yaml_metadata: dict[str, Any]) → None
```

Inject Rxiv-Maker citation into bibliography if acknowledge_rxiv_maker is true. 



**Args:**
 
 - <b>`yaml_metadata`</b>:  The YAML metadata dictionary. 


