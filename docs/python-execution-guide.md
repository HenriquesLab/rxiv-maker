# Python Execution

The guide to embedding executable Python in a manuscript (`{{py:exec}}` blocks and `{{py:get}}` inline values) lives on the website:

**[Python Execution guide →](https://rxiv-maker.henriqueslab.org/advanced/python-execution/)**

At a glance:

```markdown
{{py:exec
import pandas as pd
df = pd.read_csv("DATA/results.csv")
n = len(df)
}}

Our analysis of {{py:get n}} samples ...
```
