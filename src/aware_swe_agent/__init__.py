"""
Aware SWE Agent

An autonomous software engineering agent designed to solve real-world software issues 
by leveraging deep contextual understanding of codebases and documentation.
"""

__version__ = "0.1.0"
__author__ = "Qodo Aware Team"
__email__ = "tomer.y@qodo.ai"

from pathlib import Path

# Package root directory
PACKAGE_ROOT = Path(__file__).parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "PACKAGE_ROOT",
    "PROJECT_ROOT",
]