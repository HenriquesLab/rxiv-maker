<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `operation_ids.py`
Operation ID management for debugging and tracing. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L150"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_operation_history`

```python
get_operation_history() → OperationHistory
```

Get or create the global operation history instance. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L160"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `create_operation`

```python
create_operation(operation_type: str, **metadata) → OperationContext
```

Create a new operation context. 



**Args:**
 
 - <b>`operation_type`</b>:  Type of operation 
 - <b>`**metadata`</b>:  Additional metadata 



**Returns:**
 Operation context 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L173"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_current_operation_id`

```python
get_current_operation_id() → str | None
```

Get the ID of the most recent operation. 


---

## <kbd>class</kbd> `OperationContext`
Context manager for operation tracking with unique IDs. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L12"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(operation_type: str, metadata: dict[str, Any] | None = None)
```

Initialize operation context. 



**Args:**
 
 - <b>`operation_type`</b>:  Type of operation (e.g., "pdf_build", "validation") 
 - <b>`metadata`</b>:  Additional metadata for the operation 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L37"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `add_metadata`

```python
add_metadata(key: str, value: Any) → None
```

Add metadata to the operation. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L33"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `log`

```python
log(message: str) → None
```

Add a log entry to the operation. 


---

## <kbd>class</kbd> `OperationHistory`
Manages history of operations for debugging. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L68"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(max_operations: int = 100)
```

Initialize operation history. 



**Args:**
 
 - <b>`max_operations`</b>:  Maximum operations to keep in history 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L78"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `add_operation`

```python
add_operation(operation: OperationContext) → None
```

Add operation to history. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L140"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `clear`

```python
clear() → None
```

Clear operation history. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L108"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `generate_debug_report`

```python
generate_debug_report() → dict[str, Any]
```

Generate debug report with operation history. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L100"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_failed_operations`

```python
get_failed_operations() → list[OperationContext]
```

Get all failed operations. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L92"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_operation`

```python
get_operation(operation_id: str) → OperationContext | None
```

Get operation by ID. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L104"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_operations_by_type`

```python
get_operations_by_type(operation_type: str) → list[OperationContext]
```

Get operations by type. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/operation_ids.py#L96"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_recent_operations`

```python
get_recent_operations(count: int = 10) → list[OperationContext]
```

Get recent operations. 


