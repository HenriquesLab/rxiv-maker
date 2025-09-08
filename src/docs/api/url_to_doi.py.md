<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/url_to_doi.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `url_to_doi.py`
Utility functions for extracting DOIs from URLs. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/url_to_doi.py#L8"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `extract_doi_from_url`

```python
extract_doi_from_url(url: str) → Optional[str]
```

Extract DOI from a URL. 

This function handles various URL formats from different publishers and converts them to standard DOI format. 



**Args:**
 
 - <b>`url`</b>:  URL string that may contain a DOI 



**Returns:**
 DOI string if found, None otherwise 



**Examples:**
 ``` extract_doi_from_url("https://www.nature.com/articles/d41586-022-00563-z")```
    "10.1038/d41586-022-00563-z"

    >>> extract_doi_from_url("https://doi.org/10.1038/nature12373")
    "10.1038/nature12373"

    >>> extract_doi_from_url("https://dx.doi.org/10.1126/science.1234567")
    "10.1126/science.1234567"

    >>> extract_doi_from_url("https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0123456")
    "10.1371/journal.pone.0123456"



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/url_to_doi.py#L113"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `normalize_doi_input`

```python
normalize_doi_input(input_str: str) → str
```

Normalize input that could be either a DOI or URL containing a DOI. 



**Args:**
 
 - <b>`input_str`</b>:  Input string (DOI or URL) 



**Returns:**
 Normalized DOI string 



**Raises:**
 
 - <b>`ValueError`</b>:  If no valid DOI can be extracted 


