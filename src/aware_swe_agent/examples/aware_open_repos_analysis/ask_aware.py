#!/usr/bin/env python3
"""
Qodo Command Aware Integration Script

This script provides a Python interface to Qodo Command's Aware functionality.
It allows users to ask questions about open source repositories and get AI-powered answers.

Usage:
    python ask_aware.py "Your question here"
    python ask_aware.py "Your question here" --repos "repo1,repo2"
    python ask_aware.py --random  # Use random question from example_questions.csv

Example:
    python ask_aware.py "How do Pandas and HuggingFace Transformers manage large datasets for machine learning tasks?"
"""

import subprocess
import sys
import argparse
import os
import json
import re
import random
import csv
from datetime import datetime
from pathlib import Path


def check_qodo_installation():
    """Check if Qodo Command is installed and install if necessary."""
    try:
        result = subprocess.run(['which', 'qodo'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Qodo Command found at: {result.stdout.strip()}")
            return True
        else:
            print("✗ Qodo Command not found")
            return False
    except Exception as e:
        print(f"✗ Error checking Qodo installation: {e}")
        return False


def install_qodo():
    """Install Qodo Command using npm."""
    print("Installing Qodo Command...")
    try:
        result = subprocess.run(
            ['npm', 'install', '-g', '@qodo/command'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            print("✓ Qodo Command installed successfully")
            return True
        else:
            print(f"✗ Failed to install Qodo Command:")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Installation timed out")
        return False
    except Exception as e:
        print(f"✗ Error installing Qodo Command: {e}")
        return False


def load_random_question(script_dir):
    """
    Load a random question from the example_questions.csv file.
    
    Args:
        script_dir (Path): Directory where the script is located
    
    Returns:
        str or None: Random question or None if file not found/empty
    """
    try:
        questions_file = script_dir / "example_questions.csv"
        
        if not questions_file.exists():
            print(f"Warning: {questions_file} not found")
            return None
        
        questions = []
        with open(questions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Get the question from the 'Question' column
                if 'Question' in row and row['Question'].strip():
                    questions.append(row['Question'].strip())
        
        if not questions:
            print("Warning: No questions found in example_questions.csv")
            return None
        
        selected_question = random.choice(questions)
        print(f"🎲 Selected random question from example_questions.csv")
        return selected_question
        
    except Exception as e:
        print(f"Warning: Error loading random question: {e}")
        return None


def parse_json_response(response_text):
    """
    Parse JSON response from qodo command output.

    Args:
        response_text (str): The raw response text from qodo command

    Returns:
        dict or None: Parsed JSON data or None if parsing fails
    """
    try:
        # Look for JSON that starts with {"answer":
        json_match = re.search(r'{"answer":.*}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)

            # The key fix: preserve escaped sequences before replacing newlines
            # Use placeholders that won't appear in normal text
            placeholders = {
                '\\\\\\n': '___NEWLINE___',
                '\\\\\\r': '___CARRIAGE___',
                '\\\\\\t': '___TAB___',
                '\\\\"': '___QUOTE___',
                '\\\\\\\\': '___BACKSLASH___'
            }

            # Replace escaped sequences with placeholders
            cleaned = json_str
            for escaped, placeholder in placeholders.items():
                cleaned = cleaned.replace(escaped, placeholder)

            # Now safely replace actual newlines/whitespace
            cleaned = cleaned.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace

            # Restore escaped sequences
            for escaped, placeholder in placeholders.items():
                cleaned = cleaned.replace(placeholder, escaped)

            return json.loads(cleaned)
        return None
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse JSON response: {e}")
        return None
    except Exception as e:
        print(f"Warning: Error parsing response: {e}")
        return None


def format_answer_display(answer):
    """
    Format the answer for nice console display.
    
    Args:
        answer (str): The answer content
    
    Returns:
        str: Formatted answer for display
    """
    # Add some visual formatting
    formatted = "\n" + "="*80 + "\n"
    formatted += "ANSWER\n"
    formatted += "="*80 + "\n\n"
    formatted += answer
    formatted += "\n\n" + "="*80 + "\n"
    return formatted


def save_session_log(response_data, log_file="qodo_session.log"):
    """Save the session response to a log file."""
    try:
        log_path = Path(log_file)
        
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        # Append to log file
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Session Log - {timestamp}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Question: {response_data['question']}\n")
            if response_data['repos']:
                f.write(f"Repositories: {response_data['repos']}\n")
            f.write(f"Command: {response_data['command']}\n")
            f.write(f"Exit Code: {response_data['exit_code']}\n")
            f.write(f"\nResponse:\n{response_data['stdout']}\n")
            if response_data['stderr']:
                f.write(f"\nErrors:\n{response_data['stderr']}\n")
            f.write(f"\n{'='*80}\n")
        
        return log_path.absolute()
        
    except Exception as e:
        print(f"✗ Error saving session log: {e}")
        return None


def ask_qodo_aware(question, repos_name=None, log_file="ask_aware_session.log"):
    """
    Ask a question using Qodo Command's Aware functionality.
    
    Args:
        question (str): The question to ask
        repos_name (str, optional): Comma-separated list of repository names to focus on
        log_file (str): Path to save the session log
    
    Returns:
        dict: Response data including stdout, stderr, and exit code
    """
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Print initial user-friendly message
    print(f"🤔 Answering question: {question}")
    if repos_name:
        print(f"📚 Focusing on repositories: {repos_name}")
    print()
    
    # Build the command
    cmd = ['qodo', 'ask_open_aware','--ci', '--set', f'question={question}']
    
    if repos_name:
        cmd.extend(['--set', f'repos_name={repos_name}'])
    
    print(f"Script directory: {script_dir}")
    print(f"Executing: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        # Execute the command from the script's directory
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            cwd=script_dir  # Run from script directory
        )
        
        response_data = {
            "command": ' '.join(cmd),
            "question": question,
            "repos": repos_name or "",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
        
        # Parse JSON response if available
        json_data = parse_json_response(result.stdout) if result.stdout else None
        
        # Flag to track if we saved session log with meaningful name
        session_log_saved_with_meaningful_name = False
        
        if json_data and "answer" in json_data:
            # Extract answer from JSON
            answer = json_data["answer"]
            
            # Display formatted answer
            print(format_answer_display(answer))
            
            # Save answer to markdown file
            answer_md_path = json_data["answer_md_path"]
            if answer_md_path:
                print(f"📄 Answer saved to: {answer_md_path}")
                
                # Extract markdown file name and save session log to answers directory
                md_file_path = Path(answer_md_path)
                md_file_name = md_file_path.stem  # Get filename without extension
                answers_dir = script_dir / "answers"
                session_log_name = f"{md_file_name}_session.log"
                session_log_path = answers_dir / session_log_name
                
                # Save session log with meaningful name
                saved_log_path = save_session_log(response_data, str(session_log_path))
                if saved_log_path:
                    print(f"📝 Session log saved to: {saved_log_path}")
                    session_log_saved_with_meaningful_name = True

            
        else:
            # Fallback: display raw response
            print("Can't phrase session, Raw Response:")
            if result.stdout:
                print("Response:")
                print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            print("\nErrors/Warnings:")
            print(result.stderr)
        
        print(f"\nExit Code: {result.returncode}")
        
        # Save session log in script directory (only if not already saved with meaningful name)
        if not session_log_saved_with_meaningful_name:
            log_path = script_dir / log_file if not Path(log_file).is_absolute() else log_file
            session_log_path = save_session_log(response_data, log_path)
            if session_log_path:
                print(f"📝 Session log saved to: {session_log_path}")
        
        return response_data
        
    except subprocess.TimeoutExpired:
        error_msg = "Command timed out after 5 minutes"
        print(f"✗ {error_msg}")
        response_data = {
            "command": ' '.join(cmd),
            "question": question,
            "repos": repos_name or "",
            "stdout": "",
            "stderr": error_msg,
            "exit_code": -1
        }
        log_path = script_dir / log_file if not Path(log_file).is_absolute() else log_file
        session_log_path = save_session_log(response_data, log_path)
        if session_log_path:
            print(f"📝 Session log saved to: {session_log_path}")
        return response_data
        
    except Exception as e:
        error_msg = f"Error executing command: {e}"
        print(f"✗ {error_msg}")
        response_data = {
            "command": ' '.join(cmd),
            "question": question,
            "repos": repos_name or "",
            "stdout": "",
            "stderr": error_msg,
            "exit_code": -1
        }
        log_path = script_dir / log_file if not Path(log_file).is_absolute() else log_file
        session_log_path = save_session_log(response_data, log_path)
        if session_log_path:
            print(f"📝 Session log saved to: {session_log_path}")
        return response_data


def main():
    """Main function to handle command line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Ask questions using Qodo Command's Aware functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ask_aware.py "How do Pandas and HuggingFace Transformers manage large datasets?"
  python ask_aware.py "What are the best practices for error handling?" --repos "pandas,transformers"
  python ask_aware.py --random  # Use random question from example_questions.csv
        """
    )
    
    parser.add_argument(
        'question',
        nargs='?',  # Make question optional
        help='The question to ask about open source repositories (optional if --random is used)'
    )
    
    parser.add_argument(
        '--random',
        action='store_true',
        help='Use a random question from example_questions.csv'
    )
    
    parser.add_argument(
        '--repos',
        help='Comma-separated list of repository names to focus on (optional)'
    )
    
    parser.add_argument(
        '--log-file',
        default='qodo_session.log',
        help='Path to save the session log (default: qodo_session.log)'
    )
    
    parser.add_argument(
        '--install',
        action='store_true',
        help='Force installation of Qodo Command even if already installed'
    )
    
    args = parser.parse_args()
    
    # Determine the question to use
    if args.random:
        script_dir = Path(__file__).parent.absolute()
        question = load_random_question(script_dir)
        if not question:
            print("Failed to load random question. Please provide a question manually or check example_questions.csv")
            sys.exit(1)
    elif args.question:
        question = args.question
    else:
        print("Error: Please provide a question or use --random flag")
        parser.print_help()
        sys.exit(1)
    
    # Check if Qodo Command is installed
    if args.install or not check_qodo_installation():
        if not install_qodo():
            print("Failed to install Qodo Command. Please install manually:")
            print("npm install -g @qodo/command")
            sys.exit(1)
    
    # Ask the question
    response = ask_qodo_aware(
        question=question,
        repos_name=args.repos,
        log_file=args.log_file
    )
    
    # Exit with the same code as the qodo command
    sys.exit(response['exit_code'])


if __name__ == "__main__":
    main()