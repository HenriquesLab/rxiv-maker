<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/email_encoder.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `email_encoder.py`
Email encoding/decoding utilities for Rxiv-Maker. 

This module handles the encoding of email addresses to base64 for privacy in YAML files and their decoding for use in PDF generation. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/email_encoder.py#L12"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `encode_email`

```python
encode_email(email)
```

Encode an email address to base64. 



**Args:**
 
 - <b>`email`</b> (str):  The email address to encode 



**Returns:**
 
 - <b>`str`</b>:  Base64 encoded email address 



**Raises:**
 
 - <b>`ValueError`</b>:  If the email format is invalid 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/email_encoder.py#L39"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `decode_email`

```python
decode_email(encoded_email)
```

Decode a base64 encoded email address. 



**Args:**
 
 - <b>`encoded_email`</b> (str):  The base64 encoded email address 



**Returns:**
 
 - <b>`str`</b>:  Decoded email address 



**Raises:**
 
 - <b>`ValueError`</b>:  If the encoded email is invalid or cannot be decoded 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/email_encoder.py#L70"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `process_author_emails`

```python
process_author_emails(authors)
```

Process author list to decode any base64 encoded emails. 

This function looks for 'email64' fields in author entries and converts them to regular 'email' fields with decoded values. Regular 'email' fields are left unchanged. 



**Args:**
 
 - <b>`authors`</b> (list):  List of author dictionaries 



**Returns:**
 
 - <b>`list`</b>:  List of author dictionaries with decoded emails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/email_encoder.py#L120"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `encode_author_emails`

```python
encode_author_emails(authors)
```

Process author list to encode emails to base64. 

This function looks for 'email' fields in author entries and converts them to 'email64' fields with encoded values. 



**Args:**
 
 - <b>`authors`</b> (list):  List of author dictionaries 



**Returns:**
 
 - <b>`list`</b>:  List of author dictionaries with encoded emails 


