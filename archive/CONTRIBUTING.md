# Contributing Guidelines

Thank you for your interest in contributing to NexDatawork! We welcome all kinds of contributions, from bug reports to feature implementations.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Reporting Issues](#reporting-issues)
- [Git Workflow](#git-workflow)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

Please be respectful and inclusive. We are committed to providing a welcoming environment for everyone.

---

## How to Contribute

There are many ways to contribute:

| Contribution Type | Description |
|------------------|-------------|
| Bug Reports | Found a bug? Let us know! |
| Feature Requests | Have an idea? Share it with us |
| Documentation | Help improve our docs |
| Code | Submit bug fixes or new features |
| Testing | Help test new releases |

---

## Reporting Issues

### Before Filing an Issue

1. Check existing [bug reports](https://github.com/NexDatawork/data-agents/issues?q=is%3Aissue+label%3Abug)
2. Check [feature requests](https://github.com/NexDatawork/data-agents/issues?q=is%3Aissue+label%3Aenhancement)
3. Search closed issues for similar problems

### Bug Reports

File a bug report at: [Bug Report](https://github.com/NexDatawork/data-agents/issues/new?template=bug_report.yml)

Include:
- A reproducible test case or series of steps
- The version of the code used (commit ID)
- Any relevant modifications you made
- Your environment details (OS, Node version, Python version)

### Feature Requests

Submit feature ideas at: [Feature Request](https://github.com/NexDatawork/data-agents/issues/new?template=feature_request.yml)

---

## Git Workflow

We use a feature branch workflow. Here is how to contribute code:

### 1. Fork the Repository

```bash
# Fork via GitHub UI, then clone your fork
git clone https://github.com/YOUR_USERNAME/data-agents.git
cd data-agents

# Add upstream remote
git remote add upstream https://github.com/NexDatawork/data-agents.git
```

### 2. Create a Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create your feature branch
git checkout -b feature/your-feature-name

# For bug fixes, use:
git checkout -b fix/bug-description
```

### Branch Naming Conventions

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feature/` | New features | `feature/add-excel-support` |
| `fix/` | Bug fixes | `fix/csv-parsing-error` |
| `docs/` | Documentation | `docs/update-readme` |
| `refactor/` | Code refactoring | `refactor/agent-structure` |
| `test/` | Adding tests | `test/sql-agent-tests` |

### 3. Make Your Changes

```bash
# Make changes to the code
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add Excel file support for data upload"
```

### Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### 4. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then open a Pull Request via GitHub.

### 5. Keep Your Branch Updated

```bash
# If main has been updated, rebase your branch
git fetch upstream
git rebase upstream/main

# If there are conflicts, resolve them, then:
git add .
git rebase --continue

# Force push if needed (only on your feature branch!)
git push -f origin feature/your-feature-name
```

---

## Development Setup

### Prerequisites

- [Node.js](https://nodejs.org/en) v18+
- [Python](https://python.org) 3.10+
- [Supabase](https://supabase.com/) account (for database)
- [OpenAI](https://platform.openai.com/) or Azure OpenAI API key

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/NexDatawork/data-agents.git
cd data-agents

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Install Node.js dependencies
npm install

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Start Next.js development server
npm run dev

# Run Jupyter notebook (in separate terminal)
jupyter notebook examples/data_agent_demo.ipynb
```

---

## Code Style

### JavaScript/TypeScript

- Use Prettier for formatting
- Follow ESLint rules
- Use TypeScript for new code

### Python

- Follow PEP 8
- Use type hints where possible
- Document functions with docstrings

### General

- Write self-documenting code
- Add comments for complex logic
- Keep functions small and focused

---

## Pull Request Process

1. **Ensure your code works** - Test locally before submitting
2. **Update documentation** - If you changed functionality, update relevant docs
3. **Write clear PR description** - Explain what and why
4. **Link related issues** - Use "Closes #123" to auto-close issues
5. **Request review** - Tag maintainers for review
6. **Address feedback** - Make requested changes promptly

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow convention
- [ ] PR description is clear and complete

---

## Questions?

- Open a [Discussion](https://github.com/NexDatawork/data-agents/discussions)
- Join our [Discord](https://discord.gg/Tb55tT5UtZ)
- Check the [Wiki](https://github.com/NexDatawork/data-agents/wiki)

---

Thank you for contributing to NexDatawork!
