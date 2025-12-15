# 🐍 Python Execution Guide for Rxiv-Maker

*Complete guide to executable Python code in manuscripts - creating Jupyter notebook-like experiences with reproducible analysis*

---

## 🎯 Quick Reference

```markdown
# Initialize data and analysis (executed in order, removed from PDF)
{{py:exec
import pandas as pd
import numpy as np
from datetime import datetime

# Load your manuscript data
df = pd.read_csv("FIGURES/DATA/clinical_trial_data.csv")

# Convert date column to datetime for analysis
df['date'] = pd.to_datetime(df['date'])

# Compute analysis results directly
results = {
    'sample_size': len(df),
    'years_span': round((df['date'].max() - df['date'].min()).days / 365.25, 1),
    'correlation': np.corrcoef(df['treatment_response'], df['baseline_score'])[0, 1],
    'mean_response': df['treatment_response'].mean(),
    'std_response': df['treatment_response'].std()
}
}}

# Insert computed values into text (replaced with actual values)
Our analysis contains {{py:get results['sample_size']}} samples spanning
{{py:get results['years_span']}} years. The correlation was
r = {{py:get results['correlation']:.2f}}.
```

**Output in PDF:**
> Our analysis contains 15,847 samples spanning 16 years. The correlation was r = 0.85.

---

## 📑 Table of Contents

- [Overview & Key Concepts](#overview--key-concepts)
- [Python Command Syntax](#python-command-syntax)  
- [3-Step Execution Model](#3-step-execution-model)
- [Manuscript Data Analysis](#manuscript-data-analysis)
- [Error Handling & Debugging](#error-handling--debugging)
- [Security & Best Practices](#security--best-practices)
- [Integration with src/py Modules](#integration-with-srcpy-modules)
- [Advanced Patterns](#advanced-patterns)
- [Migration from Old Syntax](#migration-from-old-syntax)

---

## Overview & Key Concepts

### What is Python Execution in Rxiv-Maker?

Rxiv-Maker now supports **executable Python code blocks** directly within Markdown manuscripts, creating a **Jupyter notebook-like experience** for scientific writing. This enables:

- **Live Data Analysis**: Compute statistics, process datasets, and generate insights during PDF compilation
- **Dynamic Content**: Insert computed values, formatted numbers, and analysis results directly into narrative text
- **Reproducible Manuscripts**: All figures, statistics, and derived content generated programmatically
- **Version-Controlled Analysis**: Python code lives alongside manuscript text in git

### Core Principles

1. **3-Step Execution Model**: Initialization → Value Retrieval → LaTeX Conversion
2. **Context Persistence**: Variables initialized in one block available throughout the manuscript  
3. **Security Isolation**: Code executes in subprocess with restricted permissions
4. **Error Transparency**: Clear error messages with line number references for debugging
5. **PYTHONPATH Integration**: Automatic access to manuscript's `src/py/` modules

---

## Python Command Syntax

### `{{py:exec}}` - Initialization Blocks

Use for setting up data, importing modules, and performing computations:

```markdown
{{py:exec
# Import required modules
import pandas as pd
from datetime import datetime
import numpy as np

# Load and process your manuscript data
df = pd.read_csv("FIGURES/DATA/microscopy_measurements.csv")
df['date'] = pd.to_datetime(df['date'])

# Perform analysis  
total_samples = len(df)
date_range = {
    'start': df['date'].min(),
    'end': df['date'].max(),
    'span_years': (df['date'].max() - df['date'].min()).days / 365.25
}

# Statistical computations
correlation = np.corrcoef(df['x'], df['y'])[0, 1]
mean_value = df['measurement'].mean()
}}
```

**Key characteristics:**
- Executed in document order during PDF compilation
- **Removed from final PDF** - used only for initialization  
- Variables persist in context for later retrieval
- Support multi-line code with proper indentation
- Full Python syntax support (functions, classes, imports)

### `{{py:get variable}}` - Value Insertion

Use for inserting computed values into narrative text:

```markdown
Our dataset contains {{py:get total_samples}} samples collected over 
{{py:get date_range['span_years']:.1f}} years ({{py:get date_range['start'].strftime('%B %Y')}} 
to {{py:get date_range['end'].strftime('%B %Y')}}). 

The correlation coefficient was r = {{py:get correlation:.3f}}.
The mean measurement was {{py:get mean_value:.2f}} ± {{py:get df['measurement'].std():.2f}} units.
```

**Rendered output:**
> Our dataset contains 2,847 samples collected over 8.3 years (March 2015 to June 2023). The correlation coefficient was r = 0.745. The mean measurement was 12.34 ± 3.21 units.

**Key characteristics:**  
- **Replaced with actual values** in final PDF
- Support Python expressions and formatting (`:formatting_specifier`)
- Access any variable from initialization blocks
- Automatic string conversion for display

---

## 3-Step Execution Model

The Python execution system follows a strict **3-step process** for predictable, reliable behavior:

### Step 1: Execute All `{{py:exec}}` Blocks

```markdown
{{py:exec
# Block 1 - Data loading
import pandas as pd
df = pd.read_csv("FIGURES/DATA/experiment_observations.csv")
}}

Some text here...

{{py:exec  
# Block 2 - Analysis (can use df from Block 1)
summary_stats = {
    'count': len(df),
    'mean': df['value'].mean()
}
}}

More text...

{{py:exec
# Block 3 - Additional processing
formatted_count = f"{summary_stats['count']:,}"
}}
```

**Step 1 behavior:**
- All `{{py:exec}}` blocks execute **in document order**  
- Variables from earlier blocks available in later blocks
- Context builds progressively throughout the manuscript
- Errors stop execution and display helpful debugging information

### Step 2: Process All `{{py:get}}` Insertions

```markdown
# After all exec blocks complete, process all get commands:
We analyzed {{py:get formatted_count}} samples with mean {{py:get summary_stats['mean']:.2f}}.
```

**Step 2 behavior:**
- All variables from Step 1 available for retrieval
- Insertions can use any Python expressions  
- Formatting specifiers applied to numeric values
- Missing variables generate clear error messages

### Step 3: Continue with LaTeX Conversion

- All `{{py:exec}}` blocks **removed** from document
- All `{{py:get variable}}` commands **replaced** with computed values  
- Normal Rxiv-Maker processing continues (figures, citations, etc.)

### Why This Model?

**Predictable Execution Order**: No ambiguity about when code runs
**Clean Final Output**: Initialization code doesn't clutter the PDF
**Error Isolation**: Problems in one block don't affect text formatting
**Performance**: All Python execution completes before LaTeX processing

---

## Manuscript Data Analysis

### Working with CSV Data Files

Store your research data in `FIGURES/DATA/` for easy access:

```
MANUSCRIPT/
├── FIGURES/
│   └── DATA/
│       ├── experimental_results.csv
│       ├── survey_responses.csv
│       └── time_series_data.csv
└── 01_MAIN.md
```

**Loading and processing data:**

```markdown
{{py:exec
import pandas as pd
from pathlib import Path

# Load multiple datasets
results_df = pd.read_csv("FIGURES/DATA/experimental_results.csv")
survey_df = pd.read_csv("FIGURES/DATA/survey_responses.csv") 
time_df = pd.read_csv("FIGURES/DATA/time_series_data.csv")

# Data validation and cleaning
print(f"Loaded {len(results_df)} experimental results")
print(f"Loaded {len(survey_df)} survey responses")

# Process and combine data
combined_analysis = {
    'total_participants': len(survey_df['participant_id'].unique()),
    'experiments_completed': len(results_df),
    'data_collection_period': {
        'start': time_df['date'].min(),
        'end': time_df['date'].max()
    }
}

# Compute key statistics
effect_size = results_df['treatment'].mean() - results_df['control'].mean()
p_value = 0.023  # From your statistical test
}}

Our study included {{py:get combined_analysis['total_participants']}} participants 
who completed {{py:get combined_analysis['experiments_completed']}} experiments 
between {{py:get combined_analysis['data_collection_period']['start']}} and 
{{py:get combined_analysis['data_collection_period']['end']}}. 

We observed a significant treatment effect (Δ = {{py:get effect_size:.2f}}, p = {{py:get p_value}}).
```

### Real-time Data Updates

Create data updating functions in your `src/py/` modules:

```python
# src/py/data_updater.py
import requests
import pandas as pd
from io import StringIO
import numpy as np
from datetime import datetime, timedelta

def update_arxiv_data():
    """Fetch latest arXiv submission data."""
    try:
        # Simulate fetching arXiv data (replace with actual API call)
        # In reality, you'd use the actual arXiv API or stats endpoint

        # Generate sample data that looks realistic
        months = pd.date_range(start='2020-01', end='2024-09', freq='M')
        submissions = np.random.normal(15000, 2000, len(months)).astype(int)

        df = pd.DataFrame({
            'year_month': months.strftime('%Y-%m'),
            'submissions': submissions
        })

        df.to_csv("FIGURES/DATA/arxiv_submissions.csv", index=False)
        return df
    except Exception as e:
        print(f"Error updating arXiv data: {e}")
        return None

def get_latest_stats():
    """Get current statistics from updated data."""
    try:
        df = pd.read_csv("FIGURES/DATA/arxiv_submissions.csv")
        return {
            'total_submissions': int(df['submissions'].sum()),
            'latest_month': df.iloc[-1]['year_month'],
            'monthly_average': float(df['submissions'].mean())
        }
    except FileNotFoundError:
        # Return fallback values if data file doesn't exist
        return {
            'total_submissions': 850000,
            'latest_month': '2024-09',
            'monthly_average': 15000
        }
```

**Use in manuscript:**

```markdown
{{py:exec
from data_updater import update_arxiv_data, get_latest_stats

# Uncomment to fetch fresh data:
# update_arxiv_data()

# Get current statistics
stats = get_latest_stats()
last_updated = "September 2024"  # Set manually or compute
}}

This analysis uses arXiv data through {{py:get stats['latest_month']}} 
containing {{py:get stats['total_submissions']:,}} total submissions 
(last updated: {{py:get last_updated}}).
```

---

## Error Handling & Debugging

### Understanding Error Messages

When Python code fails, you'll see detailed error information in the PDF:

```
Python execution error in exec block: Initialization block execution failed (in manuscript:45): 
Error in manuscript:45: [Errno 2] No such file or directory: 'FIGURES/DATA/missing_file.csv'
```

**Error message components:**
- **Error type**: `Python execution error in exec block`
- **Location**: `manuscript:45` (file and line number)  
- **Specific error**: `No such file or directory` with problematic filename

### Common Error Patterns

#### Missing Data Files
```markdown
{{py:exec
# This will fail if file doesn't exist
df = pd.read_csv("FIGURES/DATA/nonexistent.csv")
}}
```

**Solution**: Check file paths and create missing data files:
```bash
ls -la FIGURES/DATA/  # Verify file exists  
head FIGURES/DATA/your_file.csv  # Check file content
```

#### Import Errors
```markdown
{{py:exec
# This will fail if module not installed
import some_obscure_package
}}
```

**Solution**: Install required packages or use alternative approaches:
```bash
pip install some_obscure_package
# Or use built-in alternatives
```

#### Variable Access Errors
```markdown
# In manuscript text:
The result was {{py:get undefined_variable}}.
```

**Solution**: Ensure variable defined in a `{{py:exec}}` block first:
```markdown
{{py:exec
defined_variable = "Hello World"
}}

The result was {{py:get defined_variable}}.
```

### Debugging Workflow

1. **Check PDF compilation output** for detailed error messages
2. **Verify file paths** - use relative paths from manuscript root
3. **Test Python code separately** - run code in Python interpreter first  
4. **Use print statements** in `{{py:exec}}` blocks for debugging
5. **Check line numbers** - error messages show exact location

**Debugging example:**
```markdown
{{py:exec
import pandas as pd

# Add debugging output
print("Loading data...")
try:
    df = pd.read_csv("FIGURES/DATA/experiment_observations.csv")
    print(f"Successfully loaded {len(df)} rows")
    
    # Your analysis here
    result = df['column'].mean()
    print(f"Computed result: {result}")
    
except Exception as e:
    print(f"Error in data processing: {e}")
    result = None
}}
```

---

## Security & Best Practices

### Security Model

Python code executes in a **subprocess sandbox** with:

- **Restricted module access**: Only safe, scientific computing modules allowed
- **File system limitations**: Access limited to manuscript directory  
- **Network restrictions**: External network calls require explicit approval
- **Dangerous pattern detection**: Potentially harmful code patterns blocked

### Allowed vs. Restricted Modules

#### ✅ **Safe Modules** (Always Available)
```python
# Data science & analysis
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats

# Standard library  
import json
import csv
from pathlib import Path
from datetime import datetime
import re
import math

# Manuscript utilities (automatic)
from manuscript_utils.figure_utils import *
```

#### ⚠️ **Network Modules** (Use Carefully)  
```python
import requests  # For data fetching - use sparingly
import urllib    # Web-related functionality
```

#### ❌ **Restricted Modules** (Security Risk)
```python
import os          # File system access
import subprocess  # Command execution  
import sys         # System manipulation
import importlib   # Dynamic imports
```

### Best Practices

#### 1. **Data Organization**
```
MANUSCRIPT/
├── FIGURES/
│   ├── DATA/           # Raw data files (.csv, .json)
│   ├── PLOTS/          # Generated figure files  
│   └── SCRIPTS/        # Figure generation scripts
└── src/
    └── py/             # Analysis modules (auto-imported)
        ├── analysis.py
        ├── plotting.py  
        └── utils.py
```

#### 2. **Code Structure**
```markdown
{{py:exec
# Group related functionality - replace with actual implementations
import pandas as pd
import numpy as np
from pathlib import Path

# Load data directly with error handling
def load_data(filepath):
    """Load CSV data with error handling."""
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found")
        return pd.DataFrame()

# Load data once, use multiple times
df = load_data("FIGURES/DATA/main_dataset.csv")

# Compute all needed statistics directly
if not df.empty:
    stats = {
        'mean_response': df['response_variable'].mean(),
        'std_response': df['response_variable'].std(),
        'correlation_matrix': df.select_dtypes(include=[np.number]).corr()
    }
    sample_size = len(df)

    # Calculate date range if date column exists
    if 'date' in df.columns:
        date_range = {
            'start': df['date'].min(),
            'end': df['date'].max(),
            'span_days': (pd.to_datetime(df['date'].max()) - pd.to_datetime(df['date'].min())).days
        }
    else:
        date_range = {'start': 'N/A', 'end': 'N/A', 'span_days': 0}
else:
    stats = {'mean_response': 0, 'std_response': 0}
    sample_size = 0
    date_range = {'start': 'N/A', 'end': 'N/A', 'span_days': 0}
}}
```

#### 3. **Error Prevention**
```markdown
{{py:exec
from pathlib import Path

# Check file existence before loading
data_file = Path("FIGURES/DATA/experiment_observations.csv")
if data_file.exists():
    df = pd.read_csv(data_file)
    analysis_complete = True
else:
    print(f"Warning: {data_file} not found")
    analysis_complete = False
    
# Provide fallbacks for missing data
sample_size = len(df) if analysis_complete else "N/A"
}}
```

#### 4. **Performance Optimization**
```markdown
{{py:exec
import json
from datetime import datetime
import pandas as pd
from pathlib import Path

# Generate sample data for demonstration
df = pd.DataFrame({
    'measurement': [12.3, 15.7, 11.9, 14.2, 13.8, 16.1, 12.7, 15.3]
})

# Cache expensive computations
cache_file = Path("FIGURES/DATA/.cache/analysis_results.json")

if cache_file.exists():
    # Load cached results
    with open(cache_file, 'r') as f:
        results = json.load(f)
    print("Loaded cached analysis results")
else:
    # Perform analysis and cache
    mean_val = df['measurement'].mean()
    std_val = df['measurement'].std()

    results = {
        'complex_statistic': float(std_val / mean_val),  # Coefficient of variation
        'processed_data_points': len(df),
        'mean_measurement': float(mean_val),
        'std_measurement': float(std_val),
        'analysis_timestamp': datetime.now().isoformat()
    }
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(results, f)
    print("Analysis complete, results cached")
}}
```

---

## Integration with src/py Modules

### Automatic PYTHONPATH Setup

Rxiv-Maker automatically detects and adds your manuscript's `src/py/` directory to the Python path, enabling clean module imports:

```
MANUSCRIPT/
└── src/
    └── py/                    # Automatically added to PYTHONPATH
        ├── data_processing.py
        ├── statistical_analysis.py 
        └── visualization.py
```

### Creating Analysis Modules

**Example: `src/py/data_processing.py`**
```python
"""Data processing functions for manuscript analysis."""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

def load_arxiv_data(data_file: str = "FIGURES/DATA/arxiv_submissions.csv") -> pd.DataFrame:
    """Load and validate arXiv submission data."""
    data_path = Path(data_file)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['year_month'])
    
    print(f"Loaded {len(df)} months of arXiv data")
    return df

def compute_arxiv_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute comprehensive statistics from arXiv data."""
    return {
        'total_submissions': int(df['submissions'].sum()),
        'monthly_average': float(df['submissions'].mean()),
        'peak_month': df.loc[df['submissions'].idxmax(), 'year_month'],
        'growth_rate': calculate_growth_rate(df),
        'data_span_years': (df['date'].max() - df['date'].min()).days / 365.25
    }

def calculate_growth_rate(df: pd.DataFrame) -> float:
    """Calculate annual growth rate from time series data."""
    # Your growth rate calculation logic
    return 0.15  # Example: 15% annual growth
```

### Using Modules in Manuscripts

```markdown
{{py:exec
# Implement analysis functions directly for working example
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_arxiv_data():
    """Load or generate sample arXiv submission data."""
    # Generate realistic sample data
    months = pd.date_range(start='2020-01', end='2024-09', freq='M')
    base_submissions = 15000
    trend = np.linspace(0, 5000, len(months))  # Growing trend
    noise = np.random.normal(0, 1000, len(months))
    submissions = (base_submissions + trend + noise).astype(int)

    return pd.DataFrame({
        'year_month': months.strftime('%Y-%m'),
        'date': months,
        'submissions': submissions
    })

def compute_arxiv_statistics(df):
    """Compute comprehensive statistics from arXiv data."""
    growth_rate = (df['submissions'].iloc[-1] / df['submissions'].iloc[0]) ** (1/len(df)*12) - 1

    return {
        'total_submissions': int(df['submissions'].sum()),
        'monthly_average': float(df['submissions'].mean()),
        'growth_rate': float(growth_rate),
        'data_span_years': (df['date'].max() - df['date'].min()).days / 365.25
    }

def run_trend_analysis(df):
    """Analyze submission trends over time."""
    return {
        'trend_slope': np.polyfit(range(len(df)), df['submissions'], 1)[0],
        'r_squared': np.corrcoef(range(len(df)), df['submissions'])[0,1]**2
    }

# Load and analyze data
df = load_arxiv_data()
stats = compute_arxiv_statistics(df)
trends = run_trend_analysis(df)

# Optional: Generate and save figure
plot_path = Path("FIGURES/PLOTS/arxiv_growth.svg")
plot_path.parent.mkdir(parents=True, exist_ok=True)

plt.figure(figsize=(10, 6))
plt.plot(df['date'], df['submissions'], marker='o', linewidth=2)
plt.title('arXiv Monthly Submissions Growth')
plt.xlabel('Date')
plt.ylabel('Submissions')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
plt.close()
}}

Our analysis of {{py:get stats['total_submissions']:,}} arXiv submissions 
shows an average of {{py:get stats['monthly_average']:.0f}} submissions per month
with a {{py:get stats['growth_rate']:.1%}} annual growth rate over 
{{py:get stats['data_span_years']:.1f}} years.
```

### Module Development Tips

1. **Use clear function signatures** with type hints
2. **Include comprehensive docstrings** for all functions  
3. **Handle file path edge cases** gracefully
4. **Return structured data** (dicts/dataframes) for easy access
5. **Add validation and error handling** for robust execution

---

## Advanced Patterns

### Conditional Analysis

```markdown
{{py:exec
from pathlib import Path

# Check data availability and adjust analysis accordingly
recent_data = Path("FIGURES/DATA/recent_updates.csv") 
historical_data = Path("FIGURES/DATA/historical_archive.csv")

if recent_data.exists() and historical_data.exists():
    # Full analysis with both datasets
    df_recent = pd.read_csv(recent_data)
    df_historical = pd.read_csv(historical_data)
    df_combined = pd.concat([df_historical, df_recent])
    
    analysis_type = "comprehensive"
    data_note = f"Combined analysis of {len(df_combined)} total records"
    
elif recent_data.exists():
    # Recent data only
    df_combined = pd.read_csv(recent_data)
    analysis_type = "recent_only"  
    data_note = f"Analysis limited to recent data ({len(df_combined)} records)"
    
else:
    # Fallback or error state
    analysis_type = "unavailable"
    data_note = "Data files not available - using cached results"
    
    # Load cached results or provide defaults
    cached_stats = {"mean": 42, "count": 1000}  # Example defaults
}}

## Data Analysis

{{py:get data_note}}.

<!-- Conditional content based on available analysis -->
{% if analysis_type == "comprehensive" %}
Our comprehensive analysis spanning {{py:get df_combined['date'].min()}} to 
{{py:get df_combined['date'].max()}} reveals...
{% elif analysis_type == "recent_only" %}  
Based on available recent data, our analysis shows...
{% else %}
*Note: Current analysis based on cached results due to data availability.*
{% endif %}
```

### Dynamic Figure Generation

```markdown
{{py:exec
import matplotlib.pyplot as plt
from pathlib import Path

# Generate multiple figures based on data
figure_configs = [
    {"type": "timeline", "filename": "FIGURES/PLOTS/timeline.svg"},
    {"type": "distribution", "filename": "FIGURES/PLOTS/distribution.svg"}, 
    {"type": "correlation", "filename": "FIGURES/PLOTS/correlation.svg"}
]

generated_figures = []

for config in figure_configs:
    output_path = Path(config["filename"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate figure based on type
    fig, ax = plt.subplots(figsize=(8, 6))
    
    if config["type"] == "timeline":
        ax.plot(df['date'], df['value'])
        ax.set_title("Timeline Analysis")
    elif config["type"] == "distribution":
        ax.hist(df['value'], bins=30)
        ax.set_title("Value Distribution")
    elif config["type"] == "correlation":
        ax.scatter(df['x'], df['y'])
        ax.set_title("Correlation Analysis")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    generated_figures.append(config["filename"])
    
figure_count = len(generated_figures)
}}

This analysis generated {{py:get figure_count}} figures programmatically. 
<!-- Figures will be included elsewhere in the document -->
```

### Data Validation and Quality Checks

```markdown
{{py:exec
# Comprehensive data quality assessment
def assess_data_quality(df):
    """Perform comprehensive data quality checks."""
    issues = []
    
    # Check for missing values
    missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
    if missing_pct.max() > 5:
        issues.append(f"High missing data: {missing_pct.max():.1f}% in some columns")
    
    # Check for duplicates
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        issues.append(f"{duplicate_count} duplicate records found")
        
    # Check data ranges
    if 'date' in df.columns:
        date_span = (df['date'].max() - df['date'].min()).days
        if date_span < 30:
            issues.append(f"Limited date range: only {date_span} days")
    
    return issues

# Run quality assessment
quality_issues = assess_data_quality(df)
data_quality_status = "excellent" if not quality_issues else "adequate with notes"

# Summary statistics for reporting
quality_summary = {
    'total_records': len(df),
    'completeness': f"{(1 - df.isnull().sum().sum() / df.size) * 100:.1f}%",
    'date_range_days': (df['date'].max() - df['date'].min()).days,
    'issue_count': len(quality_issues)
}
}}

## Data Quality Assessment

Our dataset contains {{py:get quality_summary['total_records']:,}} records 
with {{py:get quality_summary['completeness']}} data completeness across 
{{py:get quality_summary['date_range_days']}} days. Data quality is assessed as 
{{py:get data_quality_status}}.

{% if quality_summary['issue_count'] > 0 %}
**Data Quality Notes:**
<!-- List any identified issues -->
{% for issue in quality_issues %}
- {{py:get issue}}
{% endfor %}
{% endif %}
```

---

## Migration from Old Syntax

### Old Syntax (Deprecated)

```markdown
<!-- Old approach - no longer recommended -->
{{py:
import pandas as pd
df = pd.read_csv("FIGURES/DATA/experiment_observations.csv")

# Calculate mean for specific numeric columns
numeric_columns = df.select_dtypes(include=['number']).columns
mean_values = df[numeric_columns].mean()
overall_mean = df['measurement_value'].mean()  # Assuming 'measurement_value' column
print(f"Mean measurement value: {overall_mean:.2f}")
}}
```

### New Syntax (Current)

```markdown
<!-- New 3-step approach -->
{{py:exec
import pandas as pd
import numpy as np

df = pd.read_csv("FIGURES/DATA/experiment_observations.csv")

# Calculate specific statistical measures for the measurement column
mean_result = df['measurement_value'].mean()
std_result = df['measurement_value'].std()
sample_count = len(df)
}}

The mean measurement value in our dataset is {{py:get mean_result:.2f}} ± {{py:get std_result:.2f}} (n = {{py:get sample_count}}).
```

### Migration Steps

1. **Separate initialization from output**: Move computations to `{{py:exec}}` blocks
2. **Store values in variables**: Instead of printing, assign to variables  
3. **Use explicit value insertion**: Replace print statements with `{{py:get variable}}`
4. **Update file paths**: Use `FIGURES/DATA/` for consistency
5. **Test thoroughly**: New execution model may reveal timing issues

### Migration Example

**Before:**
```markdown
{{py:
data = [1, 2, 3, 4, 5]
mean_val = sum(data) / len(data)
std_dev = (sum((x - mean_val)**2 for x in data) / len(data))**0.5
print(f"Analysis results: mean = {mean_val}, std = {std_dev}")
}}
```

**After:**
```markdown
{{py:exec
# Statistical analysis of sample data
data = [1, 2, 3, 4, 5] 
mean_val = sum(data) / len(data)
std_dev = (sum((x - mean_val)**2 for x in data) / len(data))**0.5

# For more complex analysis, consider using numpy:
# import numpy as np
# mean_val = np.mean(data)  
# std_dev = np.std(data)
}}

Analysis results: mean = {{py:get mean_val}}, std = {{py:get std_dev:.3f}}.
```

---

## 📚 Summary & Best Practices

### Quick Checklist

- ✅ **Use `{{py:exec}}`** for all initialization and computation
- ✅ **Use `{{py:get variable}}`** to insert values into text
- ✅ **Store data in `FIGURES/DATA/`** for organization  
- ✅ **Create reusable modules in `src/py/`** for complex analysis
- ✅ **Test code independently** before including in manuscript
- ✅ **Handle errors gracefully** with try/except blocks
- ✅ **Use meaningful variable names** for clarity
- ✅ **Include data validation** for robust analysis

### Common Workflows

1. **Data Analysis Manuscripts**: Load data → Compute statistics → Generate figures → Insert values
2. **Review Articles**: Gather data from multiple sources → Synthesize → Present key findings  
3. **Technical Reports**: Process experimental data → Statistical analysis → Results presentation
4. **Grant Applications**: Current data gathering → Trend analysis → Impact projections

### Performance Tips

- **Cache expensive computations** in JSON files
- **Load data once** in early `{{py:exec}}` blocks
- **Use efficient pandas operations** instead of loops
- **Generate figures programmatically** when possible
- **Profile code execution time** for optimization

---

**📚 [User Guide](user_guide.md) | 📊 [Figures Guide](figures-guide.md) | ⚙️ [CLI Reference](cli-reference.md)**