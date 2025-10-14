<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `retry.py`
Enhanced retry utilities for network operations with exponential backoff and jitter. 

**Global Variables**
---------------
- **RETRYABLE_HTTP_CODES**
- **NON_RETRYABLE_HTTP_CODES**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L66"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `calculate_delay`

```python
calculate_delay(
    attempt: int,
    strategy: RetryStrategy = <RetryStrategy.EXPONENTIAL_BACKOFF: 'exponential_backoff'>,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) → float
```

Calculate delay for retry attempt. 



**Args:**
 
 - <b>`attempt`</b>:  Current attempt number (0-based) 
 - <b>`strategy`</b>:  Retry strategy to use 
 - <b>`base_delay`</b>:  Base delay in seconds 
 - <b>`max_delay`</b>:  Maximum delay in seconds 
 - <b>`jitter`</b>:  Whether to add random jitter to prevent thundering herd 



**Returns:**
 Delay in seconds before next attempt 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L112"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `is_retryable_error`

```python
is_retryable_error(exception: Exception) → bool
```

Determine if an exception is retryable. 



**Args:**
 
 - <b>`exception`</b>:  The exception to check 



**Returns:**
 True if the exception should be retried 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L159"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `retry_with_backoff`

```python
retry_with_backoff(
    max_attempts: int = 3,
    strategy: RetryStrategy = <RetryStrategy.EXPONENTIAL_BACKOFF: 'exponential_backoff'>,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], tuple] = <class 'Exception'>,
    on_retry: Optional[Callable[[Exception, int, float], NoneType]] = None,
    raise_on_max_attempts: bool = True
)
```

Decorator for retrying functions with exponential backoff. 



**Args:**
 
 - <b>`max_attempts`</b>:  Maximum number of retry attempts (including initial attempt) 
 - <b>`strategy`</b>:  Retry strategy to use 
 - <b>`base_delay`</b>:  Base delay in seconds 
 - <b>`max_delay`</b>:  Maximum delay in seconds 
 - <b>`jitter`</b>:  Whether to add random jitter 
 - <b>`exceptions`</b>:  Exception types to catch and retry 
 - <b>`on_retry`</b>:  Callback function called on each retry attempt 
 - <b>`raise_on_max_attempts`</b>:  Whether to raise exception after max attempts 



**Example:**
 @retry_with_backoff(max_attempts=5, strategy=RetryStrategy.EXPONENTIAL_BACKOFF) def fetch_url(url):  response = requests.get(url)  response.raise_for_status()  return response.json() 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L320"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_with_retry`

```python
get_with_retry(
    url: str,
    max_attempts: int = 3,
    timeout: int = 30,
    **kwargs
) → Response
```

Make GET request with retry logic. 



**Args:**
 
 - <b>`url`</b>:  URL to request 
 - <b>`max_attempts`</b>:  Maximum retry attempts 
 - <b>`timeout`</b>:  Request timeout 
 - <b>`**kwargs`</b>:  Additional arguments to pass to requests.get 



**Returns:**
 Response object 



**Example:**
 response = get_with_retry("https://api.crossref.org/works/10.1000/123", max_attempts=5) data = response.json() 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L340"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `post_with_retry`

```python
post_with_retry(
    url: str,
    max_attempts: int = 3,
    timeout: int = 30,
    **kwargs
) → Response
```

Make POST request with retry logic. 


---

## <kbd>class</kbd> `NonRetryableError`
Exception that indicates an operation should not be retried. 





---

## <kbd>class</kbd> `RetryStrategy`
Different retry strategies for various failure types. 





---

## <kbd>class</kbd> `RetryableError`
Exception that indicates an operation can be safely retried. 





---

## <kbd>class</kbd> `RetryableSession`
Requests session with built-in retry logic. 

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L244"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(
    max_attempts: int = 3,
    strategy: RetryStrategy = <RetryStrategy.EXPONENTIAL_BACKOFF: 'exponential_backoff'>,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    timeout: int = 30,
    user_agent: str = 'rxiv-maker/1.0 (https://github.com/henriqueslab/rxiv-maker)'
)
```

Initialize retryable session. 



**Args:**
 
 - <b>`max_attempts`</b>:  Maximum retry attempts 
 - <b>`strategy`</b>:  Retry strategy 
 - <b>`base_delay`</b>:  Base delay between retries 
 - <b>`max_delay`</b>:  Maximum delay between retries 
 - <b>`jitter`</b>:  Whether to add jitter 
 - <b>`timeout`</b>:  Request timeout in seconds 
 - <b>`user_agent`</b>:  User agent string 




---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L309"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `delete`

```python
delete(url: str, **kwargs) → Response
```

Make DELETE request with retry logic. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L297"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get`

```python
get(url: str, **kwargs) → Response
```

Make GET request with retry logic. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L313"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `json`

```python
json(method: str, url: str, **kwargs) → dict[str, Any]
```

Make request and return JSON response with retry logic. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L301"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `post`

```python
post(url: str, **kwargs) → Response
```

Make POST request with retry logic. 

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/retry.py#L305"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `put`

```python
put(url: str, **kwargs) → Response
```

Make PUT request with retry logic. 


