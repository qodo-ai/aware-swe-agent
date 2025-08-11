import logging
import docker
import uuid
import time
import tarfile
import io
import os
import tempfile
import json
import tomllib
import subprocess
import glob
from pathlib import Path
from datasets import load_dataset
from shutil import move

logging.basicConfig(level=logging.INFO)
docker_client = docker.from_env()


def get_issue_image_name(instance_id: str) -> str:
    """Fetch a docker image for the issue."""
    issue_key = instance_id.replace("__", "_1776_")
    return f"swebench/sweb.eval.x86_64.{issue_key}:latest"


def start_container(instance_id) -> str:
    """Start a docker container for the issue."""
    image_name = get_issue_image_name(instance_id)
    logging.info(f"Starting container for {instance_id}")
    client = docker.from_env()
    logging.info(f"Pulling image {image_name}")
    logging.info(f"Finished pulling image {image_name}")
    logging.info(f"Starting run for {image_name}")
    
    # Check if local package exists using glob pattern
    # Look in current directory and up one level (since script runs from scripts/test_w_swebench)
    local_packages = glob.glob("qodo-command-*.tgz") + glob.glob("../../qodo-command-*.tgz")
    install_command = "npm install -g @qodo/command"
    setup_commands = []
    
    # Debug: Log current directory and search results
    # logging.info(f"Current working directory: {os.getcwd()}")
    # logging.info(f"Searching for packages in current dir: {glob.glob('qodo-command-*.tgz')}")
    # logging.info(f"Searching for packages in parent dir: {glob.glob('../../qodo-command-*.tgz')}")
    # logging.info(f"All found packages: {local_packages}")
    
    if local_packages:
        local_package = local_packages[0]  # Use the first match
        logging.info(f"Found local package {local_package}, will install from local file")
        install_command = f"npm install -g /tmp/{os.path.basename(local_package)}"
    else:
        logging.info("Local package not found, will install from npm registry")
    
    container = client.containers.run(
        name=f"sweb.qodo.{instance_id}_{uuid.uuid4().hex[:8]}",
        image=image_name,
        detach=True,
        command=f"bash -c 'git config --global user.email a && git config --global user.name a && git config --global --add safe.directory /testbed && git commit --allow-empty -am qodo && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs && {install_command} && sleep 7200'",
    )
    
    # If using local package, copy it to the container
    if local_packages:
        local_package = local_packages[0]
        logging.info(f"Attempting to read local package: {local_package}")
        try:
            with open(local_package, 'rb') as f:
                package_data = f.read()
            _put_file_in_container(client, container.id, "/tmp", os.path.basename(local_package), package_data)
            logging.info(f"Successfully copied {local_package} to container /tmp/{os.path.basename(local_package)}")
        except Exception as e:
            logging.error(f"Failed to copy local package {local_package}: {e}")
            # Fall back to npm registry installation
            install_command = "npm install -g @qodo/command"
    
    logging.info(f"Finished startup for {image_name}")
    time.sleep(10)
    container_id = container.id
    assert container_id is not None
    logging.info(f"Started {container_id} for {instance_id}")
    return container_id


def remove_container_image(image_name: str) -> None:
    """Remove a docker image."""
    try:
        client = docker.from_env()
        client.images.remove(image=image_name, force=True)
        logging.info(f"Removed image {image_name}")
    except docker.errors.APIError as e:  # type: ignore
        logging.warning(f"Failed to remove image {image_name}: {e}")


def stop_container(container_id: str, remove_image: str = "") -> None:
    """Stop a docker container for the issue."""
    container = None
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
    except Exception as e:
        logging.info(f"Container {container_id} not found: {e}")

    if container:
        try:
            logging.info(f"Stopping container {container_id}")
            container.stop()
            logging.info(f"Stopped container {container_id}")
        except docker.errors.NotFound as e:  # type: ignore
            logging.warning(f"Failed to stop container {container_id}: {e}")
        except docker.errors.APIError as e:  # type: ignore
            logging.warning(f"Failed to stop container {container_id}: {e}")
        try:
            logging.info(f"Removing container {container_id}")
            container.remove()
            time.sleep(10)
            logging.info(f"Removed container {container_id}")
        except docker.errors.NotFound as e:  # type: ignore
            logging.warning(f"Failed to stop container {container_id}: {e}")
        except docker.errors.APIError as e:  # type: ignore
            logging.warning(f"Failed to stop container {container_id}: {e}")

    if remove_image:
        time_sleep = 20
        logging.info(f"Sleep for {time_sleep} seconds, await for docker setup")
        time.sleep(time_sleep)
        remove_container_image(remove_image)


def get_patch_output_in_container(
    container_id: str, repo_root: Path = Path("/testbed")
) -> str:
    """Generate the patch for the prediction using git diff bash command inside a Docker container."""
    cmd = [
        "docker",
        "exec",
        container_id,
        "git",
        "--no-pager",
        "diff",
        "HEAD",
    ]
    try:
        diff = subprocess.check_output(
            cmd,
            text=True,
            errors="backslashreplace",
        )
        return diff
    except Exception as e:
        logging.warning(f"Cannot run git diff command inside container: %s, {e}")
        return "Cannot run git diff command inside container"


def remove_patches_to_tests(model_patch: str) -> str:
    lines = model_patch.splitlines(keepends=True)
    filtered_lines: list[str] = []
    test_patterns = ["/test/", "/tests/", "/testing/", "test_", "tox.ini"]
    is_tests = False

    for line in lines:
        if line.startswith("diff --git a/"):
            target_path = line.split()[-1]
            is_tests = target_path.startswith("b/") and any(
                p in target_path for p in test_patterns
            )
        if not is_tests:
            filtered_lines.append(line)
    return "".join(filtered_lines)


def _put_file_in_container(client, container_id, dir_path, file_name, data_bytes):
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        tarinfo = tarfile.TarInfo(file_name)
        tarinfo.size = len(data_bytes)
        tar.addfile(tarinfo, io.BytesIO(data_bytes))
    tar_stream.seek(0)
    client.containers.get(container_id).put_archive(dir_path, tar_stream.read())
    logging.info(f"Put file {file_name} in container id {container_id}")



def get_swebench_verified_data():
    return load_dataset("SWE-bench/SWE-bench_Verified", split="test")

def get_problem_statement(instance_id):
    swebench = get_swebench_verified_data()
    filtered_instance = [entry for entry in swebench if entry['instance_id'] == instance_id]
    problem_statement = filtered_instance[0]['problem_statement'] if filtered_instance else None
    return problem_statement


def run_command_in_container(container_id: str, command: str) -> str:
    client = docker.from_env()
    container = client.containers.get(container_id)
    shell_command = f'bash -c "{command}"'
    if command != "which qodo":
        logging.info(
            f"Running command '{shell_command}' in container id {container_id}"
        )
    exec_result = container.exec_run(
        shell_command, stdout=True, stderr=True, stream=False
    )
    if hasattr(exec_result, "output") and exec_result.output:
        output_str = exec_result.output.decode()
    elif isinstance(exec_result, tuple) and len(exec_result) > 1:
        output_str = exec_result[1].decode()
    else:
        output_str = str(exec_result)
    return output_str


def create_agent_toml_in_container(
    container_id: str,
    repo_root: str,
    problem_statement: str,
    template_path: str,
    agent_command: str,
) -> str:
    logging.info(
        f"Create agent file, for command {agent_command} and template at {template_path}"
    )
    problem_statement = problem_statement.replace('"""', r'\"\"\"')
    template_toml_path = Path(template_path)
    content = template_toml_path.read_text()
    content = (
        content.replace("{problem_statement}", problem_statement)
        .replace("{agent_command}", agent_command)
        .replace("{RESEARCH_INSIGHTS}", " ")
    )
    content = content.replace("{repo_root}", "")
    client = docker.from_env()
    agents_dir = os.path.join(repo_root, "agents")
    client.containers.get(container_id).exec_run(f"mkdir -p {agents_dir}")
    instance_toml_path = os.path.join(agents_dir, f"{agent_command}.toml")
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        _put_file_in_container(
            client, container_id, agents_dir, f"{agent_command}.toml", f.read()
        )
    os.unlink(tmp_path)
    root_agent_toml_path = os.path.join(repo_root, "agent.toml")
    import_path = f"agents/{agent_command}.toml"
    exit_code, _ = client.containers.get(container_id).exec_run(
        f"test -f {root_agent_toml_path}"
    )
    if exit_code != 0:
        root_content = (
            "# Version of the agent configuration standard\n"
            'version = "1.0"\n'
            f'imports = ["{import_path}"]\n'
        )
        _put_file_in_container(
            client, container_id, repo_root, "agent.toml", root_content.encode()
        )
    else:
        exit_code, output = client.containers.get(container_id).exec_run(
            f"cat {root_agent_toml_path}"
        )
        if exit_code == 0:
            try:
                import io
                data = tomllib.load(io.BytesIO(output))
                imports = data.get("imports", [])
                if import_path not in imports:
                    imports.append(import_path)
                version = data.get("version", "1.0")
                root_content = (
                    "# Version of the agent configuration standard\n"
                    f'version = "{version}"\n'
                    f"imports = {json.dumps(imports)}\n"
                )
                _put_file_in_container(
                    client, container_id, repo_root, "agent.toml", root_content.encode()
                )
            except Exception as e:
                print(f"Failed to parse agent.toml in container: {e}")
    return instance_toml_path


def _run_swe_harness(
    predictions_path: Path,
    instance_ids: list[str] | None,
    report_dir: Path,
    max_workers: int,
    run_id: str,
    force_rebuild: bool = False,
    namespace="swebench",
):
    from swebench.harness.run_evaluation import (
        main as swe_main,
    )
    swe_main(
        dataset_name="princeton-nlp/SWE-bench_Verified",
        split="test",
        instance_ids=instance_ids,
        predictions_path=str(predictions_path),
        run_id=run_id,
        report_dir=str(report_dir),
        max_workers=max_workers,
        open_file_limit=4096,
        timeout=1_800,
        force_rebuild=force_rebuild,
        cache_level="env",
        clean=False,
        namespace=namespace,
        instance_image_tag="latest",
        rewrite_reports=False,
        modal=False,
    )
    src = next(Path().glob(f"*{run_id}.json"), None)
    if src:
        move(src, Path(report_dir) / f"{run_id}.report.json")


def check_resolved_instances(report_path):
    with open(report_path, "r") as f:
        data = json.load(f)
    if data["resolved_instances"] == data["total_instances"]:
        return 1
    else:
        return 0
