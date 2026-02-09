# Git Hands-On Exercises

## Overview

Practice everything you've learned by building a Python calculator project with Git. You'll initialize a repository, create branches, handle merge conflicts, and open a Pull Request.

**Duration:** ~20 minutes

## Exercise 1: Initialize and First Commits

### Goal
Create a repository and make your first commits.

### Steps

```bash
# 1. Create project directory
mkdir git-calculator
cd git-calculator

# 2. Initialize Git
git init

# 3. Create main.py with basic structure
cat > main.py << 'EOF'
"""
Simple Calculator CLI
"""

def main():
    print("Calculator v1.0")
    print("Commands: add, subtract, quit")

if __name__ == "__main__":
    main()
EOF

# 4. Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc
*.pyo
.Python

# Virtual environment
venv/
env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
EOF

# 5. Create README
cat > README.md << 'EOF'
# Calculator CLI

A simple command-line calculator built with Python.

## Features
- Addition
- Subtraction

## Usage
```bash
python main.py
```
EOF

# 6. Stage and commit initial structure
git add .
git status
git commit -m "Initial commit: project structure

Add main.py with CLI skeleton.
Add .gitignore for Python project.
Add README with basic documentation."

# 7. View your commit
git log --oneline
```

### Verify

```bash
# Should see:
# - 1 commit
# - All files tracked
# - Clean working directory

git status
# Output: nothing to commit, working tree clean
```

## Exercise 2: Feature Branch - Add Function

### Goal
Create a branch and implement the add function.

### Steps

```bash
# 1. Create and switch to feature branch
git switch -c feature/add-function

# 2. Add the add function
cat > calculator.py << 'EOF'
"""
Calculator operations
"""

def add(a, b):
    """Add two numbers"""
    return a + b
EOF

# 3. Update main.py to use it
cat > main.py << 'EOF'
"""
Simple Calculator CLI
"""
from calculator import add

def main():
    print("Calculator v1.0")
    print("Commands: add, subtract, quit")
    
    # Example usage
    result = add(5, 3)
    print(f"5 + 3 = {result}")

if __name__ == "__main__":
    main()
EOF

# 4. Test it works
python main.py
# Should print: 5 + 3 = 8

# 5. Commit the feature
git add calculator.py
git commit -m "Add calculator module with add function"

git add main.py
git commit -m "Integrate add function into CLI"

# 6. View history
git log --oneline
```

### Verify

```bash
# Should see 3 commits on feature/add-function
git log --oneline
```

## Exercise 3: Parallel Work - Simulate Conflict

### Goal
Simulate a teammate working on main, creating a merge conflict.

### Steps

```bash
# 1. Switch back to main
git switch main

# 2. Verify you're on main (calculator.py shouldn't exist here)
ls
# Should NOT show calculator.py

# 3. Create subtract function on main (simulating teammate)
cat > calculator.py << 'EOF'
"""
Calculator operations
"""

def subtract(a, b):
    """Subtract two numbers"""
    return a - b
EOF

# 4. Update main.py to use subtract
cat > main.py << 'EOF'
"""
Simple Calculator CLI
"""
from calculator import subtract

def main():
    print("Calculator v1.0")
    print("Commands: add, subtract, quit")
    
    # Example usage
    result = subtract(10, 4)
    print(f"10 - 4 = {result}")

if __name__ == "__main__":
    main()
EOF

# 5. Commit on main
git add calculator.py main.py
git commit -m "Add subtract function on main branch"

# 6. View divergent history
git log --oneline --graph --all
```

### Verify

```bash
# Should see:
# - main has subtract
# - feature/add-function has add
# - Both modified the same files (conflict coming!)
```

## Exercise 4: Merge and Resolve Conflict

### Goal
Merge feature branch and resolve the conflict.

### Steps

```bash
# 1. Merge feature into main
git merge feature/add-function

# Output:
# Auto-merging main.py
# CONFLICT (content): Merge conflict in main.py
# Auto-merging calculator.py
# CONFLICT (content): Merge conflict in calculator.py
# Automatic merge failed; fix conflicts and then commit the result.

# 2. Check status
git status
# Unmerged paths:
#   both modified:   calculator.py
#   both modified:   main.py

# 3. View conflicts
cat calculator.py
```

### Conflict in calculator.py

```python
"""
Calculator operations
"""

<<<<<<< HEAD
def subtract(a, b):
    """Subtract two numbers"""
    return a - b
=======
def add(a, b):
    """Add two numbers"""
    return a + b
>>>>>>> feature/add-function
```

### Resolution

```bash
# 4. Resolve calculator.py - keep both functions
cat > calculator.py << 'EOF'
"""
Calculator operations
"""

def add(a, b):
    """Add two numbers"""
    return a + b

def subtract(a, b):
    """Subtract two numbers"""
    return a - b
EOF
```

### Conflict in main.py

```python
"""
Simple Calculator CLI
"""
<<<<<<< HEAD
from calculator import subtract
=======
from calculator import add
>>>>>>> feature/add-function

def main():
    print("Calculator v1.0")
    print("Commands: add, subtract, quit")
    
    # Example usage
<<<<<<< HEAD
    result = subtract(10, 4)
    print(f"10 - 4 = {result}")
=======
    result = add(5, 3)
    print(f"5 + 3 = {result}")
>>>>>>> feature/add-function

if __name__ == "__main__":
    main()
```

### Resolution

```bash
# 5. Resolve main.py - use both functions
cat > main.py << 'EOF'
"""
Simple Calculator CLI
"""
from calculator import add, subtract

def main():
    print("Calculator v1.0")
    print("Commands: add, subtract, quit")
    
    # Example usage
    print(f"5 + 3 = {add(5, 3)}")
    print(f"10 - 4 = {subtract(10, 4)}")

if __name__ == "__main__":
    main()
EOF

# 6. Test the resolved code
python main.py
# Output:
# Calculator v1.0
# Commands: add, subtract, quit
# 5 + 3 = 8
# 10 - 4 = 6

# 7. Stage resolved files
git add calculator.py main.py

# 8. Check status
git status
# All conflicts fixed but you are still merging.

# 9. Complete the merge
git commit -m "Merge feature/add-function into main

Resolved conflicts by combining both functions.
Both add and subtract now available."

# 10. View history
git log --oneline --graph
```

### Verify

```bash
# Should see:
# - Merge commit
# - Both functions in calculator.py
# - Code runs correctly
```

## Exercise 5: Add Tests (Bonus)

### Goal
Add unit tests for the calculator.

### Steps

```bash
# 1. Create test file
cat > test_calculator.py << 'EOF'
"""
Unit tests for calculator
"""
import pytest
from calculator import add, subtract

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
    assert subtract(10, 10) == 0
EOF

# 2. Update README with testing instructions
cat >> README.md << 'EOF'

## Testing

Install pytest:
```bash
pip install pytest
```

Run tests:
```bash
pytest test_calculator.py
```
EOF

# 3. Commit tests
git add test_calculator.py README.md
git commit -m "Add unit tests for calculator

Add pytest tests for add and subtract functions.
Update README with testing instructions."
```

## Exercise 6: Push to GitHub (Optional)

### Goal
Create a GitHub repository and push your code.

### Steps

```bash
# 1. Create repository on GitHub
# Go to github.com → New Repository
# Name: git-calculator
# Don't initialize with README (we have one)

# 2. Add remote
git remote add origin https://github.com/YOUR_USERNAME/git-calculator.git

# 3. Push main branch
git push -u origin main

# 4. View on GitHub
# Open: https://github.com/YOUR_USERNAME/git-calculator
```

## Exercise 7: Feature PR Workflow (Optional)

### Goal
Practice the full PR workflow.

### Steps

```bash
# 1. Create multiply feature branch
git switch -c feature/multiply-function

# 2. Add multiply function
cat >> calculator.py << 'EOF'

def multiply(a, b):
    """Multiply two numbers"""
    return a * b
EOF

# 3. Add test
cat >> test_calculator.py << 'EOF'

def test_multiply():
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0
    assert multiply(-2, 3) == -6
EOF

# 4. Commit changes
git add calculator.py test_calculator.py
git commit -m "Add multiply function with tests"

# 5. Push branch
git push -u origin feature/multiply-function

# 6. Open PR on GitHub
# Go to repository → "Compare & pull request"
# Fill in description
# Click "Create pull request"

# 7. After review, merge PR on GitHub

# 8. Update local main
git switch main
git pull origin main

# 9. Delete local feature branch
git branch -d feature/multiply-function
```

## Challenge Exercise: Division with Error Handling

### Your Task

Implement division with these requirements:

1. Create `feature/divide-function` branch
2. Add `divide(a, b)` function
3. Handle division by zero (raise `ValueError`)
4. Add comprehensive tests (including error case)
5. Update main.py to demonstrate division
6. Commit with good messages
7. Merge to main (may need to resolve conflicts)

### Solution (Spoiler)

<details>
<summary>Click to reveal solution</summary>

```bash
# 1. Create branch
git switch -c feature/divide-function

# 2. Add divide function
cat >> calculator.py << 'EOF'

def divide(a, b):
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
EOF

# 3. Add tests
cat >> test_calculator.py << 'EOF'

def test_divide():
    assert divide(6, 2) == 3
    assert divide(5, 2) == 2.5
    assert divide(0, 5) == 0

def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(5, 0)
EOF

# 4. Update main.py
# (Add divide example)

# 5. Commit
git add calculator.py test_calculator.py main.py
git commit -m "Add divide function with zero handling

- Implement divide with error checking
- Raise ValueError for division by zero
- Add comprehensive tests including error case"

# 6. Merge to main
git switch main
git merge feature/divide-function

# 7. Run tests
pytest test_calculator.py
```

</details>

## Key Concepts Practiced

- ✓ `git init` - Initialize repository
- ✓ `git add` / `git commit` - Stage and commit
- ✓ `git switch -c` - Create branches
- ✓ `git log --graph` - View history
- ✓ `git merge` - Merge branches
- ✓ **Conflict resolution** - Manual merge
- ✓ `git push` - Upload to GitHub
- ✓ **Pull Requests** - Team collaboration

## What You've Learned

1. **Complete Git workflow** - Init → branch → commit → merge
2. **Conflict resolution** - Hands-on practice
3. **Good commit messages** - Clear, descriptive
4. **Branch management** - Feature branches, cleanup
5. **GitHub integration** - Push, PRs, collaboration

## Next Steps

1. **Create more features** - Add power, modulo, etc.
2. **Practice PRs** - Open more pull requests
3. **Collaborate** - Work with a friend on the same repo
4. **Explore history** - Use `git log`, `git blame`
5. **Try advanced features** - Rebase, cherry-pick, stash

## Congratulations!

You've completed the Git course. You now have the skills to:
- Version control your code professionally
- Collaborate with teams using branches and PRs
- Resolve conflicts confidently
- Use Git in data engineering workflows
- Integrate Git with your IDE

**Keep practicing!** Git mastery comes from daily use.

---

**Navigation:**
- **Previous:** [11 - VSCode Git Guide](11-vscode-git-guide.md)
- **Home:** [Git Course Overview](README.md)
