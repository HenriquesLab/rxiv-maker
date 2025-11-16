<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `github.py`
GitHub integration utilities for rxiv-maker repository management. 

This module provides GitHub CLI (gh) integration for creating, cloning, and managing manuscript repositories on GitHub. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_gh_cli_installed`

```python
check_gh_cli_installed() → bool
```

Check if GitHub CLI (gh) is installed. 



**Returns:**
  True if gh CLI is available in PATH 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L32"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_gh_auth`

```python
check_gh_auth() → bool
```

Check if user is authenticated with GitHub CLI. 



**Returns:**
  True if authenticated 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L53"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_git_installed`

```python
check_git_installed() → bool
```

Check if git is installed. 



**Returns:**
  True if git is available in PATH 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L62"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `check_github_repo_exists`

```python
check_github_repo_exists(org: str, repo_name: str) → bool
```

Check if a GitHub repository exists. 



**Args:**
 
 - <b>`org`</b>:  GitHub organization or username 
 - <b>`repo_name`</b>:  Repository name 



**Returns:**
 True if repository exists 



**Raises:**
 
 - <b>`GitHubError`</b>:  If gh CLI is not available or not authenticated 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L95"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `create_github_repo`

```python
create_github_repo(org: str, repo_name: str, visibility: str = 'public') → str
```

Create a new GitHub repository. 



**Args:**
 
 - <b>`org`</b>:  GitHub organization or username 
 - <b>`repo_name`</b>:  Repository name 
 - <b>`visibility`</b>:  'public' or 'private' 



**Returns:**
 Repository URL 



**Raises:**
 
 - <b>`GitHubError`</b>:  If creation fails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L159"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `clone_github_repo`

```python
clone_github_repo(org: str, repo_name: str, target_path: Path) → None
```

Clone a GitHub repository. 



**Args:**
 
 - <b>`org`</b>:  GitHub organization or username 
 - <b>`repo_name`</b>:  Repository name 
 - <b>`target_path`</b>:  Target directory path 



**Raises:**
 
 - <b>`GitHubError`</b>:  If cloning fails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L199"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `list_github_repos`

```python
list_github_repos(org: str, pattern: str = 'manuscript-') → List[Dict[str, str]]
```

List GitHub repositories matching a pattern. 



**Args:**
 
 - <b>`org`</b>:  GitHub organization or username 
 - <b>`pattern`</b>:  Repository name pattern to match 



**Returns:**
 List of repository dictionaries with 'name' and 'url' keys 



**Raises:**
 
 - <b>`GitHubError`</b>:  If listing fails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L246"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `setup_git_remote`

```python
setup_git_remote(
    repo_path: Path,
    remote_url: str,
    remote_name: str = 'origin'
) → None
```

Add a git remote to a repository. 



**Args:**
 
 - <b>`repo_path`</b>:  Path to git repository 
 - <b>`remote_url`</b>:  Remote repository URL 
 - <b>`remote_name`</b>:  Name for the remote (default: origin) 



**Raises:**
 
 - <b>`GitHubError`</b>:  If adding remote fails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L300"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `push_to_remote`

```python
push_to_remote(
    repo_path: Path,
    branch: str = 'main',
    remote_name: str = 'origin'
) → None
```

Push commits to remote repository. 



**Args:**
 
 - <b>`repo_path`</b>:  Path to git repository 
 - <b>`branch`</b>:  Branch name to push 
 - <b>`remote_name`</b>:  Remote name 



**Raises:**
 
 - <b>`GitHubError`</b>:  If push fails 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/src/rxiv_maker/utils/github.py#L335"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_github_orgs`

```python
get_github_orgs() → List[str]
```

Get list of GitHub organizations the user has access to. 



**Returns:**
  List of organization names 



**Raises:**
 
 - <b>`GitHubError`</b>:  If retrieval fails 


---

## <kbd>class</kbd> `GitHubError`
Exception for GitHub operation errors. 





