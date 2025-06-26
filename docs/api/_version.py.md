<!-- markdownlint-disable -->

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `_version.py`
Git implementation of _version.py. 

**Global Variables**
---------------
- **LONG_VERSION_PY**
- **HANDLERS**

---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L22"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_keywords`

```python
get_keywords() → dict[str, str]
```

Get the keywords needed to look up the version information. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L46"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_config`

```python
get_config() → VersioneerConfig
```

Create, populate and return the VersioneerConfig() object. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L68"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `register_vcs_handler`

```python
register_vcs_handler(vcs: str, method: str) → Callable
```

Create decorator to mark a method as the handler of a VCS. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `run_command`

```python
run_command(
    commands: list[str],
    args: list[str],
    cwd: Optional[str] = None,
    verbose: bool = False,
    hide_stderr: bool = False,
    env: Optional[dict[str, str]] = None
) → tuple[Optional[str], Optional[int]]
```

Call the given command(s). 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L133"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `versions_from_parentdir`

```python
versions_from_parentdir(
    parentdir_prefix: str,
    root: str,
    verbose: bool
) → dict[str, Any]
```

Try to determine the version from the parent directory name. 

Source tarballs conventionally unpack into a directory that includes both the project name and a version string. We will also support searching up two directory levels for an appropriately named parent directory 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L166"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `git_get_keywords`

```python
git_get_keywords(versionfile_abs: str) → dict[str, str]
```

Extract version information from the given file. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L194"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `git_versions_from_keywords`

```python
git_versions_from_keywords(
    keywords: dict[str, str],
    tag_prefix: str,
    verbose: bool
) → dict[str, Any]
```

Get version information from git keywords. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L269"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `git_pieces_from_vcs`

```python
git_pieces_from_vcs(
    tag_prefix: str,
    root: str,
    verbose: bool,
    runner: Callable = <function run_command at 0x106227560>
) → dict[str, Any]
```

Get version from 'git describe' in the root of the source tree. 

This only gets called if the git-archive 'subst' keywords were *not* expanded, and _version.py hasn't already been rewritten with a short version string, meaning we're inside a checked out source tree. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L411"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `plus_or_dot`

```python
plus_or_dot(pieces: dict[str, Any]) → str
```

Return a + if we don't already have one, else return a . 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L418"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `render_pep440`

```python
render_pep440(pieces: dict[str, Any]) → str
```

Build up version string, with post-release "local version identifier". 

Our goal: TAG[+DISTANCE.gHEX[.dirty]] . Note that if you get a tagged build and then dirty it, you'll get TAG+0.gHEX.dirty 

Exceptions: 1: no tags. git_describe was just HEX. 0+untagged.DISTANCE.gHEX[.dirty] 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L442"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `render_pep440_branch`

```python
render_pep440_branch(pieces: dict[str, Any]) → str
```

TAG[[.dev0]+DISTANCE.gHEX[.dirty]] . 

The ".dev0" means not master branch. Note that .dev0 sorts backwards (a feature branch will appear "older" than the master branch). 

Exceptions: 1: no tags. 0[.dev0]+untagged.DISTANCE.gHEX[.dirty] 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L471"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `pep440_split_post`

```python
pep440_split_post(ver: str) → tuple[str, Optional[int]]
```

Split pep440 version string at the post-release segment. 

Returns the release segments before the post-release and the post-release version number (or -1 if no post-release segment is present). 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L481"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `render_pep440_pre`

```python
render_pep440_pre(pieces: dict[str, Any]) → str
```

TAG[.postN.devDISTANCE] -- No -dirty. 

Exceptions: 1: no tags. 0.post0.devDISTANCE 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L505"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `render_pep440_post`

```python
render_pep440_post(pieces: dict[str, Any]) → str
```

TAG[.postDISTANCE[.dev0]+gHEX] . 

The ".dev0" means dirty. Note that .dev0 sorts backwards (a dirty tree will appear "older" than the corresponding clean one), but you shouldn't be releasing software with -dirty anyways. 

Exceptions: 1: no tags. 0.postDISTANCE[.dev0] 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L532"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `render_pep440_post_branch`

```python
render_pep440_post_branch(pieces: dict[str, Any]) → str
```

TAG[.postDISTANCE[.dev0]+gHEX[.dirty]] . 

The ".dev0" means not master branch. 

Exceptions: 1: no tags. 0.postDISTANCE[.dev0]+gHEX[.dirty] 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L561"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `render_pep440_old`

```python
render_pep440_old(pieces: dict[str, Any]) → str
```

TAG[.postDISTANCE[.dev0]] . 

The ".dev0" means dirty. 

Exceptions: 1: no tags. 0.postDISTANCE[.dev0] 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L583"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `render_git_describe`

```python
render_git_describe(pieces: dict[str, Any]) → str
```

TAG[-DISTANCE-gHEX][-dirty]. 

Like 'git describe --tags --dirty --always'. 

Exceptions: 1: no tags. HEX[-dirty]  (note: no 'g' prefix) 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L603"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `render_git_describe_long`

```python
render_git_describe_long(pieces: dict[str, Any]) → str
```

TAG-DISTANCE-gHEX[-dirty]. 

Like 'git describe --tags --dirty --always -long'. The distance/hash is unconditional. 

Exceptions: 1: no tags. HEX[-dirty]  (note: no 'g' prefix) 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L623"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `render`

```python
render(pieces: dict[str, Any], style: str) → dict[str, Any]
```

Render the given version pieces into the requested style. 


---

<a href="https://github.com/henriqueslab/rxiv-maker/blob/main/src/py/_version.py#L665"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_versions`

```python
get_versions() → dict[str, Any]
```

Get version information or return default if unable to do so. 


---

## <kbd>class</kbd> `NotThisMethod`
Exception raised if a method is not valid for the current scenario. 





---

## <kbd>class</kbd> `VersioneerConfig`
Container for Versioneer configuration parameters. 





