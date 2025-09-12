<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `unicode_safe.py`
Unicode-safe console output utilities for rxiv-maker. 

This module provides cross-platform safe console output functions that handle Unicode encoding issues on Windows and other systems with limited Unicode support. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L16"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `supports_unicode`

```python
supports_unicode() → bool
```

Check if the current environment supports Unicode characters. 



**Returns:**
 
 - <b>`bool`</b>:  True if Unicode is supported, False otherwise 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L49"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_safe_icon`

```python
get_safe_icon(emoji: str, fallback: str) → str
```

Get a safe icon that works across different terminals. 



**Args:**
 
 - <b>`emoji`</b>:  Unicode emoji to use if supported 
 - <b>`fallback`</b>:  ASCII fallback if Unicode is not supported 



**Returns:**
 
 - <b>`str`</b>:  The appropriate icon for the current environment 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L62"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `convert_to_ascii`

```python
convert_to_ascii(message: str) → str
```

Convert Unicode emoji and symbols to ASCII equivalents. 



**Args:**
 
 - <b>`message`</b>:  The message to convert 



**Returns:**
 ASCII-safe version of the message 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L130"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `safe_print`

```python
safe_print(message: str, **kwargs) → None
```

Print a message with Unicode safety fallbacks. 



**Args:**
 
 - <b>`message`</b>:  The message to print 
 - <b>`**kwargs`</b>:  Additional arguments to pass to print() 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L153"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `safe_console_print`

```python
safe_console_print(
    console,
    message: str,
    style: str | None = None,
    **kwargs
) → None
```

Print a message using Rich console with cross-platform Unicode fallback. 



**Args:**
 
 - <b>`console`</b>:  Rich console instance 
 - <b>`message`</b>:  The message to print 
 - <b>`style`</b>:  Rich style to apply 
 - <b>`**kwargs`</b>:  Additional arguments to pass to console.print 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L183"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `print_success`

```python
print_success(message: str) → None
```

Print a success message with safe Unicode handling. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L189"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `print_error`

```python
print_error(message: str) → None
```

Print an error message with safe Unicode handling. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L195"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `print_warning`

```python
print_warning(message: str) → None
```

Print a warning message with safe Unicode handling. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L201"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `print_info`

```python
print_info(message: str) → None
```

Print an info message with safe Unicode handling. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L208"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `console_success`

```python
console_success(console, message: str) → None
```

Print a success message using Rich console with safe Unicode handling. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L214"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `console_error`

```python
console_error(console, message: str) → None
```

Print an error message using Rich console with safe Unicode handling. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L220"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `console_warning`

```python
console_warning(console, message: str) → None
```

Print a warning message using Rich console with safe Unicode handling. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/unicode_safe.py#L226"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `console_info`

```python
console_info(console, message: str) → None
```

Print an info message using Rich console with safe Unicode handling. 


