# SWE-bench Verified Benchmark with Claude-4.1-Opus

This directory contains the implementation for running the **SWE-bench Verified** benchmark using the **Claude-4.1-Opus** model through the Qodo Command CLI agent.

## 🎯 Overview

SWE-bench Verified is a curated subset of the SWE-bench dataset containing 500 high-quality, manually verified software engineering problems. This implementation leverages the Claude-4.1-Opus model to autonomously solve real-world GitHub issues across various Python repositories.

## 📊 Model Configuration

- **Model**: `claude-4-sonnet`
- **Max Iterations**: 500
- **Benchmark Dataset**: SWE-bench Verified (500 instances)
- **Evaluation Framework**: Official SWE-bench harness
- **Container Environment**: Docker-based isolated testing

## 🏗️ Architecture

```
swebench_verified/
├── run_swe_instance.py      # Single instance execution
├── run_swe_instances.py     # Batch processing
├── utils.py                 # Core utilities and Docker management
├── template_qodo_command_swe_agent.toml  # Agent configuration
├── find_swe_batch.py        # Batch discovery utilities
└── logs/                    # Execution logs and results
    └── run_evaluation/      # Evaluation reports
```

## 🚀 Quick Start

### Prerequisites

1. **Docker**: Ensure Docker is installed and running
2. **Qodo API Key**: Set your API key in `.env` file:
   ```bash
   QODO_API_KEY=your_api_key_here
   ```
3. **Python Dependencies**: Install required packages:
   ```bash
   pip install datasets docker python-dotenv swebench
   ```

### Running a Single Instance

```bash
cd src/benchmarks/swebench_verified
python run_swe_instance.py <instance_id> [--run_id <custom_run_id>]
```

**Example:**
```bash
python run_swe_instance.py django__django-11099
```

### Running Multiple Instances

```bash
python run_swe_instances.py <instance_id1> <instance_id2> ... [options]
```

**Options:**
- `--max_workers`: Maximum workers for SWE-bench harness (default: 1)
- `--max_concurrency`: Maximum parallel predictions (default: 1)
- `--run_id`: Custom run identifier

**Example:**
```bash
python run_swe_instances.py django__django-11099 requests__requests-2317 --max_concurrency 2 --run_id my_batch_run
```

## 🔧 Configuration

### Agent Configuration (`template_qodo_command_swe_agent.toml`)

The agent is configured with:
- **Sequential thinking** for complex problem analysis
- **Shell execution** for running tests and commands
- **Filesystem operations** for code exploration and modification
- **Ripgrep** for efficient code search

### Key Features:
- 8-step systematic problem-solving approach
- Mandatory bug reproduction before fixing
- Comprehensive testing and verification
- Root cause analysis with sequential thinking
- Test-driven development practices

## 📈 Evaluation Process

1. **Problem Analysis**: Agent reads the GitHub issue description
2. **Environment Setup**: Docker container with repository and dependencies
3. **Bug Reproduction**: Create scripts to reproduce the reported issue
4. **Root Cause Analysis**: Use sequential thinking to identify the core problem
5. **Fix Implementation**: Apply targeted code modifications
6. **Verification**: Run reproduction scripts and existing tests
7. **Test Creation**: Add new tests to prevent regression
8. **Evaluation**: Official SWE-bench harness validates the solution

## 📊 Output Structure

```
logs/run_evaluation/<run_id>/
├── preds_<instance_id>.json     # Predictions for single instance
├── preds.json                   # Batch predictions
├── <run_id>.report.json         # Evaluation report
└── session_<instance_id>.txt    # Detailed execution logs
```

### Prediction Format
```json
{
  "instance_id": "django__django-11099",
  "model_patch": "diff --git a/file.py b/file.py\n...",
  "model_name_or_path": "swe_eval_qodo_command"
}
```

### Report Format
```json
{
  "total_instances": 1,
  "resolved_instances": 1,
  "success_rate": 1.0
}
```

## 🐳 Docker Integration

The system automatically:
- Pulls SWE-bench Docker images for each instance
- Installs Node.js and Qodo Command CLI
- Configures Git settings for patch generation
- Manages container lifecycle (start/stop/cleanup)
- Handles local package installation if available

### Container Naming Convention
```
sweb.qodo.<instance_id>_<random_hash>
```
