<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/text_utils.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `text_utils.py`
Text processing utilities for rxiv-maker. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/text_utils.py#L7"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `count_words_in_text`

```python
count_words_in_text(text: Optional[str]) → int
```

Count words in text, excluding code blocks and LaTeX commands. 

This function provides robust word counting for academic manuscripts by filtering out code blocks, inline code, and LaTeX commands. 



**Args:**
 
 - <b>`text`</b>:  The text to count words in. Can be None. 



**Returns:**
 
 - <b>`int`</b>:  Number of words found in the text. 



**Examples:**
 ``` count_words_in_text("Hello world")```
    2
    >>> count_words_in_text("Hello `code` world")
    2
    >>> count_words_in_text("Hello \\textbf{bold} world")
    2



---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/text_utils.py#L47"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `clean_text_for_analysis`

```python
clean_text_for_analysis(text: Optional[str]) → str
```

Clean text by removing code blocks and LaTeX commands for analysis. 



**Args:**
 
 - <b>`text`</b>:  The text to clean. Can be None. 



**Returns:**
 
 - <b>`str`</b>:  Cleaned text with code and LaTeX removed. 


