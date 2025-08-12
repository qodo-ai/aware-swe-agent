import sys
import logging
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .run_swe_instance import predict, eval

def run_predictions(instance_ids, predictions_path, session_logs_dir, max_concurrency):
    futures = []
    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        for instance_id in instance_ids:
            futures.append(executor.submit(predict, instance_id, predictions_path, session_logs_dir))
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Prediction failed: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run multiple SWE instances in parallel.")
    parser.add_argument("instance_ids", nargs='+', help="List of instance IDs to process.")
    parser.add_argument("--max_workers", type=int, default=1, help="Max workers for swebench harness.")
    parser.add_argument("--max_concurrency", type=int, default=1, help="Max parallel predictions.")
    parser.add_argument("--run_id", type=str, default=None, help="Run ID for organizing output files.")
    args = parser.parse_args()
    
    # Generate run_id if not provided
    if args.run_id is None:
        args.run_id = f"qodo_command_{random.randint(1000, 9999)}"
    
    # Create output directory structure
    script_dir = Path(__file__).parent.resolve()
    output_dir = script_dir / "logs" / "run_evaluation" / args.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set paths for outputs
    predictions_path = output_dir / "preds.json"
    
    logging.info(f"Using run_id: {args.run_id}")
    logging.info(f"Output directory: {output_dir}")
    
    run_predictions(args.instance_ids, predictions_path, output_dir, args.max_concurrency)
    eval(predictions_path, args.instance_ids, args.max_workers, args.run_id, output_dir)

if __name__ == "__main__":
    main()