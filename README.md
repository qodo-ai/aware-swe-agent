# 🧠 Aware SWE Agent

An **autonomous software engineering agent** designed to solve real-world software issues by leveraging deep contextual understanding of codebases and documentation. This repository demonstrates and open-sources **Qodo Aware** capabilities through comprehensive benchmarking tools and practical examples.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-green" />
  <img src="https://img.shields.io/github/license/qodo-ai/aware-swe-agent" />
  <img src="https://img.shields.io/badge/Qodo-Aware-orange" />
</p>

---

## 🚀 Key Features

- 💡 **Context-Aware Intelligence**  
  Ingests full repositories, issues, and documentation to build a deep contextual map.


- 🧩 **Modular Autonomy Stack**  
  Incorporates planning, code reading, generation, and validation modules.



- 🛠️ **Aware Integration**  
  Built on top of [Qodo Aware](https://aware.dev) for high-fidelity static + dynamic code understanding.


- 🔄 **Multi-Step Autonomy**  
  Supports iterative task decomposition, planning, execution, and evaluation loops.

---
## 📦 Installation

### Quick Start

```bash
git clone git@github.com:qodo-ai/aware-swe-agent.git
cd aware-swe-agent

# Install the package and dependencies
pip install -e .

# Install Qodo Command
npm install -g @qodo/command

# Login to Qodo Command
qodo login

# Optional: for SWE-bench instances evaluation  - set up also QODO_API_KEY
echo "QODO_API_KEY=your_api_key_here" > .env
```
### Validate Installation with Qodo Aware analysis example

```bash
#Use random example questions:
ask-aware --random
```

### Prerequisites

- **Python 3.11+**
- **Node.js and npm** (for Qodo Command)
- **Docker** (optional, for SWE-bench evaluation)
- **Qodo User**

---

## 🧪 Usage

## 🎯 Examples: Open Source Repository Analysis

The `src/examples/aware_open_repos_analysis` directory showcases **Qodo Aware's** powerful capabilities for analyzing and understanding open source repositories. This comprehensive example demonstrates how to:

### 🔍 **Intelligent Repository Analysis**
- **25+ Supported Repositories** including React, Angular, Pandas, HuggingFace Transformers, FastAPI, Flask, and more
- **AI-Powered Question Answering** about code patterns, architecture, and best practices
- **Comparative Analysis** between different frameworks and libraries

### 📝 **Pre-built Example Questions**
The system includes 10 carefully crafted example questions covering:
- **Framework Comparisons**: "How do React and Angular handle state management?"
- **Library Analysis**: "How do Pandas and HuggingFace Transformers manage large datasets?"
- **Architecture Patterns**: "What are the best practices for error handling?"
- **Performance Analysis**: "Compare templating engines performance"
- **Integration Strategies**: "How do Flask and FastAPI handle background tasks?"

### 📊 **Generated Outputs**
Each query produces:
- Session log file 
- A markdown file with the research output

### 🚀 **Getting Started with Examples**
```bash
# Try a framework comparison
ask-aware "Compare Flask and FastAPI for building APIs"

# Analyze specific repositories
ask-aware "How does error handling work?" --repos "pandas,transformers"

# Use a random example question
ask-aware --random

# See all supported repositories (from the examples directory)
cat src/aware_swe_agent/examples/aware_open_repos_analysis/open_source_supported_repos.csv
```

This example demonstrates the power of **Qodo Aware** in understanding complex codebases and providing intelligent, contextual answers about software engineering practices across the open source ecosystem.

---

### SWE-bench Benchmarking

**Run a single instance:**
```bash
aware-swe-run-instance astropy__astropy-14309
```

**Run multiple instances:**
```bash
aware-swe-run-instances astropy__astropy-14309 django__django-11179 --max_concurrency 2
```

**Find batch instances:**
```bash
aware-swe-find-batch
```

### Aware Integration Examples

**Ask questions about open source repositories:**
```bash
ask-aware "How do React and Angular handle state management?"
```

**Use random example questions:**
```bash
ask-aware --random
```

**Focus on specific repositories:**
```bash
ask-aware "What are the best practices for error handling?" --repos "pandas,transformers"
```
---

## 📊 Benchmarks

| Benchmark              | Qodo-SWE-Agent | SWE-agent (baseline) | 
|------------------------|----------------|----------------------|
| **SWE-bench Verified** | **72.4%**      | 70.4%                | 
| **DeepCodeBench**      | **TBD**        | TBD                  |


> 📌 SWE-bench Verified contains 500 high-quality, manually verified software engineering problems from real GitHub issues.

> 📌 DeepCodeBench new benchmark dataset of real-world questions derived from large, complex code repositories.

**📖 Learn More:** 
- Read our detailed blog post about [How Qodo Command Achieved 72.4% on SWE-bench Verified](https://www.qodo.ai/blog/qodo-command-swe-bench-verified/) to understand our approach and methodology.
- TBD - add DeepCodeBench blog post 
---
### SWE-bench Agent Configuration

The agent uses a Plan and Solve systematic approach:
1. **Problem Analysis** - Read and understand the GitHub issue
2. **Bug Reproduction** - Create scripts to reproduce the reported issue
3. **Root Cause Analysis** - Use sequential thinking to identify core problems
4. **Fix Implementation** - Apply targeted code modifications

---

## 📁 Project Structure

```
aware-swe-agent/
│
├── src/
│   ├── benchmarks/
│   │   └── swebench_verified/     # SWE-bench Verified benchmark implementation
│   │       ├── run_swe_instance.py      # Single instance execution
│   │       ├── run_swe_instances.py     # Batch processing
│   │       ├── utils.py                 # Docker management utilities
│   │       ├── template_qodo_command_swe_agent.toml  # Agent configuration
│   │       └── logs/                    # Execution logs and results
│   │
│   └── examples/
│       └── aware_open_repos_analysis/   # Aware integration examples
│           ├── ask_aware.py             # Main script for asking questions
│           ├── agent.toml               # Agent configuration
│           ├── example_questions.csv    # Sample questions
│           ├── open_source_supported_repos.csv  # Supported repositories
│           ├── agents/                  # Agent configurations
│           └── answers/                 # Generated answers and reports
│
├── .env                    # Environment variables
├── LICENSE                 # MIT License
└── README.md              # This file
```




<p align="center">
  Built with 💚 by the Qodo Team<br>
  <em>Empowering developers with AI-driven software engineering</em>
</p>