<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/progress.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `progress.py`
Progress indicators for installation process. 



---

## <kbd>class</kbd> `ProgressIndicator`
Progress indicator for installation tasks. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/progress.py#L13"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(verbose: bool = False)
```

Initialize progress indicator. 



**Args:**
 
 - <b>`verbose`</b>:  Enable verbose output 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/progress.py#L39"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `complete_task`

```python
complete_task(success: bool = True)
```

Complete the current task. 



**Args:**
 
 - <b>`success`</b>:  Whether the task succeeded 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/progress.py#L98"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `show_progress_bar`

```python
show_progress_bar(current: int, total: int, prefix: str = '')
```

Show a progress bar. 



**Args:**
 
 - <b>`current`</b>:  Current progress 
 - <b>`total`</b>:  Total items 
 - <b>`prefix`</b>:  Prefix text 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/progress.py#L25"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `start_task`

```python
start_task(task_name: str)
```

Start a new task with progress indication. 



**Args:**
 
 - <b>`task_name`</b>:  Name of the task 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/install/utils/progress.py#L66"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `update_progress`

```python
update_progress(message: str)
```

Update progress with a message. 



**Args:**
 
 - <b>`message`</b>:  Progress message 


