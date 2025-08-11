import os
import json
import subprocess
import shutil
import random
from utils import get_swebench_verified_data

def clone_repo_to_tmp():
    tmp_dir = '/tmp/swebench_repo'
    repo_url = 'https://github.com/SWE-bench/experiments.git'

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    subprocess.run(['git', 'clone', repo_url, tmp_dir])
    return tmp_dir


def get_resolved_instances_from_json(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    return set(data.get("resolved", []))


def find_swe_batch(k=10, n_easy=5, n_medium=0, n_hard=0, p_medium=0.5):
    tmp_dir = clone_repo_to_tmp()
    verified_dir = os.path.join(tmp_dir, 'evaluation', 'verified')

    subdirs = [d for d in os.listdir(verified_dir) if os.path.isdir(os.path.join(verified_dir, d))]
    subdirs.sort(reverse=True)
    recent_submissions = subdirs[:k]
    resolved_sets = []

    print("Processing the following submissions:")
    for subdir in recent_submissions:
        print(f"- {subdir}")
        results_json_path = os.path.join(verified_dir, subdir, 'results', 'results.json')
        if os.path.exists(results_json_path):
            resolved_instances = get_resolved_instances_from_json(results_json_path)
            resolved_sets.append(resolved_instances)
        else:
            resolved_sets.append(set())

    # Count how many times each instance was solved in the last k submissions
    instance_solved_count = {}
    for idx, resolved in enumerate(resolved_sets):
        for instance in resolved:
            instance_solved_count[instance] = instance_solved_count.get(instance, 0) + 1
    all_instances = set()
    for resolved in resolved_sets:
        all_instances.update(resolved)
    # Also include instances that were never solved
    swebench = get_swebench_verified_data()
    for entry in swebench:
        all_instances.add(entry['instance_id'])

    easy, medium, hard = [], [], []
    lower = int((p_medium - 0.2) * k)
    upper = int((p_medium + 0.2) * k)
    for instance in all_instances:
        count = instance_solved_count.get(instance, 0)
        if count == k:
            easy.append(instance)
        elif count == 0:
            hard.append(instance)
        elif lower <= count <= upper:
            medium.append(instance)

    print(f"Found {len(easy)} easy, {len(medium)} medium, {len(hard)} hard instances to select from.")
    # Sample up to the requested number from each group
    selected_easy = random.sample(easy, min(n_easy, len(easy))) if easy else []
    selected_medium = random.sample(medium, min(n_medium, len(medium))) if medium else []
    selected_hard = random.sample(hard, min(n_hard, len(hard))) if hard else []

    if len(selected_easy) < n_easy:
        print(f"Warning: Only found {len(selected_easy)} easy instances (requested {n_easy})")
    if len(selected_medium) < n_medium:
        print(f"Warning: Only found {len(selected_medium)} medium instances (requested {n_medium})")
    if len(selected_hard) < n_hard:
        print(f"Warning: Only found {len(selected_hard)} hard instances (requested {n_hard})")

    result = selected_easy + selected_medium + selected_hard
    print(f"Returned: {len(selected_easy)} easy, {len(selected_medium)} medium, {len(selected_hard)} hard instances.")

    shutil.rmtree(tmp_dir)
    return result

# Example usage
if __name__ == "__main__":
    # Default behavior
    instances = find_swe_batch(k=10, n_easy=5, n_medium=0, n_hard=0, p_medium=0.5)
    print("Selected instances:", instances)
