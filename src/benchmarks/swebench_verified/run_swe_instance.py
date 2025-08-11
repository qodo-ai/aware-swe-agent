import os
import sys
import time
import logging
import random
from pathlib import Path
from dotenv import load_dotenv
import json
from utils import (
    get_problem_statement,
    start_container,
    create_agent_toml_in_container,
    run_command_in_container,
    get_patch_output_in_container,
    remove_patches_to_tests,
    stop_container,
    _run_swe_harness,
    check_resolved_instances,
)

load_dotenv()
model = "claude-4-sonnet"
max_iter = 500
script_dir = Path(__file__).parent.resolve()
logs_path = script_dir / "logs"
template_path  = script_dir / "template_qodo_command_swe_agent.toml"

# These will be set per instance in main()
predictions_path = None
report_path = None

def predict(instance_id, predictions_path, session_logs_dir=None):
    import threading
    problem_statement = get_problem_statement(instance_id)
    container_id = start_container(instance_id)
    create_agent_toml_in_container(
        container_id=container_id,
        repo_root="/testbed",
        problem_statement=problem_statement,
        template_path=str(template_path),
        agent_command="solve"
    )

    # pull docker for instance, install npm and qodo command
    time_to_docker_setup = 0
    while True:
        which_qodo = run_command_in_container(container_id, "which qodo")
        if which_qodo:
            break
        time_limit = 90
        if time_to_docker_setup > time_limit:
            logging.warning(
                f"Qodo CLI not found in container after {time_limit} seconds, container_id {container_id}, stopping setup"
            )
            stop_container(container_id)
            raise RuntimeError(
                f"Qodo CLI not found in container after {time_limit} seconds, container_id {container_id}"
            )
        iteration_sleep_time = 5
        time.sleep(iteration_sleep_time)
        time_to_docker_setup += iteration_sleep_time
    logging.info(
        f"Qodo CLI setup completed after {time_to_docker_setup} seconds, container_id {container_id}, instance id {instance_id}"
    )

    # run prediction for instance

    load_dotenv()
    QODO_API_KEY = os.getenv("QODO_API_KEY")  # Loaded from .env if running locally
    cmd = f"export QODO_API_KEY={QODO_API_KEY} && qodo solve --ci --model={model} --max_iterations={max_iter} --debug"
    session = run_command_in_container(container_id, cmd)
    # save session log
    if session_logs_dir is None:
        session_logs_dir = logs_path
    else:
        session_logs_dir = Path(session_logs_dir)
    session_logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = session_logs_dir / f"session_{instance_id}.txt"
    with log_path.open("w", encoding="utf-8") as f:
        f.write("\n")
        f.write(session)
    # extract patch of code diffs
    model_patch = get_patch_output_in_container(container_id)
    patch = remove_patches_to_tests(model_patch)
    stop_container(container_id)
    time.sleep(5)
    # save pred to shared file (thread-safe)
    pred = {
        "instance_id": instance_id,
        "model_patch": patch,
        "model_name_or_path": "swe_eval_qodo_command"
    }
    lock_path = str(predictions_path) + ".lock"
    lock = threading.Lock()
    with lock:
        # File lock for thread safety
        try:
            import portalocker
        except ImportError:
            portalocker = None
        if portalocker:
            with open(lock_path, "w") as lockfile:
                portalocker.lock(lockfile, portalocker.LOCK_EX)
                if predictions_path.exists():
                    with open(predictions_path, "r") as f:
                        all_preds = json.load(f)
                else:
                    all_preds = {}
                all_preds[instance_id] = pred
                with open(predictions_path, "w") as f:
                    json.dump(all_preds, f, indent=2)
                portalocker.unlock(lockfile)
        else:
            # Fallback: not process-safe, but thread-safe
            if predictions_path.exists():
                with open(predictions_path, "r") as f:
                    all_preds = json.load(f)
            else:
                all_preds = {}
            all_preds[instance_id] = pred
            with open(predictions_path, "w") as f:
                json.dump(all_preds, f, indent=2)
    logging.info(f"Predict for instance {instance_id} completed")
    return

def eval(predictions_path, instance_ids, max_workers=1, run_id=None, report_dir=None):
    # Use provided run_id or generate one
    if run_id is None:
        run_id = f"qodo_command_batch"
    if report_dir is None:
        report_dir = script_dir
    
    _run_swe_harness(
        predictions_path=predictions_path,
        instance_ids=instance_ids,
        report_dir=report_dir,
        max_workers=max_workers,
        run_id=run_id,
    )
    logging.info(f"Evaluation for instances {instance_ids} completed")
    return

def main():
    global predictions_path, report_path
    
    import argparse
    parser = argparse.ArgumentParser(description="Run a single SWE instance.")
    parser.add_argument("instance_id", help="Instance ID to process.")
    parser.add_argument("--run_id", type=str, default=None, help="Run ID for organizing output files.")
    args = parser.parse_args()
    
    instance_id = args.instance_id
    
    # Generate run_id if not provided
    if args.run_id is None:
        args.run_id = f"qodo_command_{random.randint(1000, 9999)}"
    
    # Create output directory structure
    parent_dir = script_dir.parent  # aware-swe-agent directory
    output_dir = parent_dir / "logs" / "run_evaluation" / args.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set paths for outputs
    predictions_path = output_dir / f"preds_{instance_id}.json"
    report_path = output_dir / f"{args.run_id}.report.json"
    
    logging.info(f"Using run_id: {args.run_id}")
    logging.info(f"Output directory: {output_dir}")
    
    predict(instance_id, predictions_path, output_dir)
    eval(predictions_path, [instance_id], max_workers=1, run_id=args.run_id, report_dir=output_dir)
    
    # Debug: Check if report file exists before trying to read it
    if not report_path.exists():
        print(f"Error: Report file not found at {report_path}")
        print("Files in directory:")
        for file in output_dir.glob("*.json"):
            print(f"  - {file}")
        sys.exit(1)
    
    is_resolved = check_resolved_instances(report_path)
    print(is_resolved)
    # Convert to proper shell exit codes: 0 = success, 1 = failure
    if is_resolved == 1:
        sys.exit(0)  # All instances resolved = success
    else:
        sys.exit(1)  # Some instances unresolved = failure

if __name__ == "__main__":
    main()

