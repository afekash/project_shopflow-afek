# Creating a Python Project

## What is a Python Project?

At its simplest, a Python "project" is just:

1. A directory with Python files (`.py`)
2. A Python interpreter that can run those files
3. (Usually) a way to manage dependencies

There's no magical "create project" command or special project file format required. If you have a folder with `main.py` in it, you have a project.

However, as projects grow beyond simple scripts, you need structure. This lesson covers how to set up a project that scales from prototype to production.

## Creating a Project From Scratch

Let's create a basic Python project:

```python
import os
from pathlib import Path

# Create project structure
project_root = Path("my_data_pipeline")
project_root.mkdir(exist_ok=True)

# Create source directory
src_dir = project_root / "src" / "my_data_pipeline"
src_dir.mkdir(parents=True, exist_ok=True)

# Create a simple module
init_file = src_dir / "__init__.py"
init_file.write_text('"""My data pipeline package."""\n__version__ = "0.1.0"\n')

# Create main entry point
main_file = src_dir / "main.py"
main_file.write_text('''def run():
    print("Pipeline running!")

if __name__ == "__main__":
    run()
''')

print(f"Created project at: {project_root.absolute()}")
```

You now have:

```
my_data_pipeline/
└── src/
    └── my_data_pipeline/
        ├── __init__.py
        └── main.py
```

## Virtual Environments: Why They Exist

**Problem**: Python installs packages globally by default. If project A needs `pandas==1.5.0` and project B needs `pandas==2.0.0`, they conflict.

**Solution**: Virtual environments isolate each project's dependencies.

A virtual environment is just a directory containing:
- A copy of the Python interpreter (or symlinks to it)
- A `site-packages/` folder for installed packages
- Scripts to "activate" it (modify your `PATH`)

### Creating a Virtual Environment

```python
import subprocess
import sys
from pathlib import Path

project_root = Path("my_data_pipeline")

# Create virtual environment
venv_path = project_root / ".venv"
if not venv_path.exists():
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    print(f"Created virtual environment at: {venv_path}")
else:
    print("Virtual environment already exists")
```

After creating, activate it in your shell:

```bash
# On macOS/Linux
source my_data_pipeline/.venv/bin/activate

# On Windows
my_data_pipeline\.venv\Scripts\activate
```

Your prompt changes to show `(.venv)`, indicating the virtual environment is active. Now `pip install` only affects this project.

### What Happens Under the Hood?

When you activate a virtual environment:

1. Your `PATH` is modified to prioritize `.venv/bin/` (or `.venv\Scripts\` on Windows)
2. Running `python` now uses the virtual environment's interpreter
3. Running `pip` installs to `.venv/lib/python3.X/site-packages/`

**Advanced Note:** You don't need to activate to use a virtual environment. You can directly run `.venv/bin/python script.py`. Activation is just a shell convenience. Tools like `uv` and CI/CD pipelines often skip activation entirely.

## Running Python Code

There are two main ways to run Python code:

### 1. Script Execution

```bash
python main.py
```

This runs `main.py` as a script. The `__name__` variable is set to `"__main__"`, which is why you see:

```python
if __name__ == "__main__":
    # This block runs when executed as a script
    run()
```

### 2. Module Execution

```bash
python -m my_data_pipeline.main
```

This runs `main.py` as a module within the `my_data_pipeline` package. Key differences:

- Python adds the current directory to `sys.path`, making imports work correctly
- Useful for packages with relative imports
- How tools like `pytest`, `pip`, and `uvicorn` are typically invoked

**Example showing the difference:**

```python
# save as: my_data_pipeline/src/my_data_pipeline/utils.py
def greet():
    return "Hello from utils!"
```

```python
# save as: my_data_pipeline/src/my_data_pipeline/main.py
from .utils import greet  # Relative import

def run():
    print(greet())

if __name__ == "__main__":
    run()
```

From `my_data_pipeline/src/`:

```bash
# This fails with "ImportError: attempted relative import with no known parent package"
python my_data_pipeline/main.py

# This works
python -m my_data_pipeline.main
```

## Project Layout Conventions

There are two common Python project layouts:

### 1. Flat Layout

```
my_project/
├── my_project/
│   ├── __init__.py
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
├── pyproject.toml
└── README.md
```

**When to use**: Small projects, scripts, learning exercises.

### 2. Src Layout

```
my_project/
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── main.py
│       └── utils.py
├── tests/
│   └── test_main.py
├── pyproject.toml
└── README.md
```

**When to use**: Production code, packages you'll distribute, anything that needs robust testing.

**Why `src/` is better for production:**

1. **Import hygiene**: Forces you to install your package to test it, preventing "it works on my machine" bugs
2. **Namespace clarity**: Makes it obvious what's part of your package vs external dependencies
3. **Build safety**: Prevents accidentally importing unbuilt/uninstalled code

```python
# Demonstrating the difference
import sys
from pathlib import Path

# In flat layout, this works even without installing the package:
sys.path.insert(0, str(Path("my_project")))
import my_project  # Imports from source directly

# In src layout, you must install first:
# python -m pip install -e .
# Then import my_project works correctly
```

For data engineering projects that will be deployed to production (containers, scheduled jobs, shared libraries), use the src layout.

## Advanced: `__init__.py` and `__main__.py`

### `__init__.py`

This file marks a directory as a Python package. It runs when you import the package:

```python
# src/my_data_pipeline/__init__.py
"""My data pipeline package."""

__version__ = "0.1.0"

# You can expose commonly-used classes/functions at package level
from .main import run
from .utils import greet

__all__ = ["run", "greet", "__version__"]
```

Now users can do:

```python
from my_data_pipeline import run, __version__
print(__version__)  # "0.1.0"
run()
```

Instead of:

```python
from my_data_pipeline.main import run
```

### `__main__.py`

This makes your package executable with `python -m package_name`:

```python
# src/my_data_pipeline/__main__.py
from .main import run

if __name__ == "__main__":
    run()
```

Now you can run:

```bash
python -m my_data_pipeline
# Executes __main__.py, which calls run()
```

This is how tools like `pip` work: `python -m pip install ...` runs `pip/__main__.py`.

## Import Resolution

Python searches for imports in `sys.path`, which includes:

1. The directory containing the script you ran
2. `PYTHONPATH` environment variable directories
3. Standard library directories
4. Installed packages in `site-packages/`

```python
import sys
print("Python searches for imports in these directories:")
for path in sys.path:
    print(f"  {path}")
```

**Common gotcha**: If you have a file named `random.py` in your project directory, `import random` imports your file instead of the standard library. Always avoid naming conflicts with stdlib modules.

## Summary

| Concept | Key Points |
|---------|-----------|
| **Python Project** | Just a directory with `.py` files, interpreter, and dependencies |
| **Virtual Environment** | Isolates project dependencies; created with `python -m venv` |
| **Running Code** | Script: `python file.py`; Module: `python -m package.module` |
| **Project Layout** | Flat for small projects; `src/` layout for production code |
| **`__init__.py`** | Marks directory as package; controls what `import package` exposes |
| **`__main__.py`** | Makes package runnable with `python -m package` |

## Next Steps

Now that you understand project structure, the next lesson covers **dependency management**: how to declare, install, and lock your project's dependencies using `pip` and modern alternatives like `uv`.

---

**Navigation:**
- **Previous**: [← Course Home](../README.md)
- **Next**: [Dependency Management →](02-dependency-management.md)
- **Home**: [Python Essentials](../README.md)
