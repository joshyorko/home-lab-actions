"""
Kubernetes Actions for Home Lab

This module provides AI Actions to interact with Kubernetes clusters.
It uses the official Python Kubernetes client to manage pods, deployments, and other resources.
"""

from sema4ai.actions import action
from kubernetes import client, config
from typing import Optional
import logging
import os
import subprocess
from dotenv import load_dotenv
import json
import re
from .models import (
    PodResponse, PodLogResponse, NamespaceResponse,
    ClusterInfoResponse, PodDeleteResponse, VMResponse, VMListResponse,DeploymentListResponse,
    RancherContextResponse, KubeConfigResponse, KubeControlResponse,RancherResponseSet
)

# Explicitly load the .env file from the specified path
load_dotenv("/home/kdlocpanda/second_brain/Areas/RPA/home-lab-actions/.env")

logger = logging.getLogger(__name__)

_KUBECONFIG_PATH = os.path.expanduser("~/.kube/config")

def _load_config():
    """
    Try in-cluster first, fall back to the downloaded kubeconfig path.
    This handles both development (local kubeconfig) and production (in-cluster) scenarios.
    """
    try:
        # Try to load in-cluster configuration first (when running inside a k8s pod)
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration")
    except config.ConfigException:
        try:
            config.load_kube_config(config_file=_KUBECONFIG_PATH)
            logger.info(f"Loaded Kubernetes configuration from: {_KUBECONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to load Kubernetes configuration: {e}")
            raise

@action(is_consequential=False)
def list_pods(namespace: Optional[str] = "default") -> PodResponse:
    """
    List all Pods in the given namespace.
    
    Args:
        namespace (str, optional): The namespace to list pods from. Defaults to "default".
        
    Returns:
        PodResponse: List of pods with their status
    """
    try:
        _load_config()
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace)
        
        if not pods.items:
            return PodResponse(
                result="No pods found in namespace",
                namespace=namespace,
                pod_count=0,
                pods=[]
            )
        
        pod_list = []
        for pod in pods.items:
            status = pod.status.phase
            created_time = pod.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") if pod.metadata.creation_timestamp else "Unknown"
            pod_list.append({
                "name": pod.metadata.name,
                "status": status,
                "created": created_time
            })
        
        result = f"Pods in namespace '{namespace}'\n"
        result += f"Total pods: {len(pods.items)}\n"
        for pod in pod_list:
            result += f"- {pod['name']} | {pod['status']} | Created: {pod['created']}\n"
        
        return PodResponse(
            result=result,
            namespace=namespace,
            pod_count=len(pods.items),
            pods=pod_list
        )
        
    except Exception as e:
        error_msg = f"Failed to list pods in namespace '{namespace}': {str(e)}"
        logger.error(error_msg)
        return PodResponse(
            error=error_msg,
            namespace=namespace,
            pod_count=0,
            pods=[]
        )

@action(is_consequential=False)
def get_pod_logs(pod_name: str, namespace: Optional[str] = "default", tail_lines: Optional[int] = 50) -> PodLogResponse:
    """
    Get logs from a specific pod.
    
    Args:
        pod_name (str): The name of the pod to get logs from
        namespace (str, optional): The namespace of the pod. Defaults to "default".
        tail_lines (int, optional): Number of lines to tail from the end. Defaults to 50.
        
    Returns:
        PodLogResponse: The pod logs and metadata
    """
    try:
        _load_config()
        v1 = client.CoreV1Api()
        
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines
        )
        
        result = f"Pod Logs: {pod_name}\n"
        result += f"Namespace: {namespace}\n"
        result += f"Lines shown: Last {tail_lines} lines\n\n"
        result += logs
        
        return PodLogResponse(
            result=result,
            pod_name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines if tail_lines is not None else 50,
            logs=logs
        )
        
    except Exception as e:
        error_msg = f"Failed to get logs from pod '{pod_name}' in namespace '{namespace}': {str(e)}"
        logger.error(error_msg)
        return PodLogResponse(
            error=error_msg,
            pod_name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines if tail_lines is not None else 50
        )


@action(is_consequential=False)
def list_namespaces() -> NamespaceResponse:
    """
    List all namespaces in the cluster.
    
    Returns:
        NamespaceResponse: A list of namespace names and count
    """
    try:
        _load_config()
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()
        
        namespace_names = [ns.metadata.name for ns in namespaces.items]
        
        result = "OK"
      
        
        return NamespaceResponse(
            result=result,
            total_namespaces=len(namespace_names),
            namespaces=namespace_names
        )
        
    except Exception as e:
        error_msg = f"Failed to list namespaces: {str(e)}"
        logger.error(error_msg)
        return NamespaceResponse(
            error=error_msg,
            total_namespaces=0,
            namespaces=[]
        )

@action(is_consequential=False)
def list_deployments(namespace: Optional[str] = "default") -> DeploymentListResponse:
    """
    List all deployments in the given namespace.
    
    Args:
        namespace (str, optional): The namespace to list deployments from. Defaults to "default".
        
    Returns:
        DeploymentListResponse: A list of deployments with their status
    """
    try:
        _load_config()
        apps_v1 = client.AppsV1Api()
        deployments = apps_v1.list_namespaced_deployment(namespace)
        
        if not deployments.items:
            return DeploymentListResponse(
                result=f"No deployments found in namespace {namespace}",
                namespace=namespace,
                deployment_count=0,
                deployments=[]
            )
        
        deployment_list = []
        for deployment in deployments.items:
            name = deployment.metadata.name
            replicas = deployment.spec.replicas or 0
            available = deployment.status.available_replicas or 0
            deployment_list.append({
                "name": name,
                "desired_replicas": replicas,
                "available_replicas": available,
                "health": "Healthy" if available == replicas else "Degraded" if available > 0 else "Unhealthy"
            })
        
        result = f"Deployments in namespace {namespace}\n"
        result += f"Total deployments: {len(deployments.items)}\n\n"
        for dep in deployment_list:
            result += f"- {dep['name']} | {dep['health']} | {dep['available_replicas']}/{dep['desired_replicas']} replicas\n"
        
        return DeploymentListResponse(
            result=result,
            namespace=namespace,
            deployment_count=len(deployment_list),
            deployments=deployment_list
        )
        
    except Exception as e:
        error_msg = f"Failed to list deployments in namespace '{namespace}': {str(e)}"
        logger.error(error_msg)
        return DeploymentListResponse(
            error=error_msg,
            namespace=namespace,
            deployment_count=0,
            deployments=[]
        )

def _strip_ansi_codes(text: str) -> str:
    """Removes ANSI escape codes from a string."""
    if not text:
        return ""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

@action(is_consequential=False)
def get_cluster_info() -> ClusterInfoResponse:
    """
    Get detailed information about the Kubernetes cluster.
    
    Returns:
        ClusterInfoResponse: Cluster information including control plane and core services status
    """
    try:
        _load_config()
        v1 = client.CoreV1Api()
        version_api = client.VersionApi()
        
        k8s_version = "Unknown"
        try:
            version_info = version_api.get_code()
            if isinstance(version_info, object) and hasattr(version_info, 'git_version'):
                k8s_version = getattr(version_info, 'git_version')
            else:
                logger.warning(f"Could not get git_version from version_info object. Got: {version_info}")
        except Exception as e:
            logger.warning(f"Could not get version from API, falling back to kubectl: {e}")
            try:
                version_cmd = ["kubectl", "version", "--short"]
                version_result = subprocess.run(version_cmd, capture_output=True, text=True)
                if version_result.returncode == 0:
                    for line in version_result.stdout.splitlines():
                        if "Server Version" in line:
                            k8s_version = line.split(": ")[-1].strip()
                            break
                else:
                    logger.warning(f"kubectl version --short failed: {version_result.stderr}")
            except FileNotFoundError:
                logger.error("kubectl command not found.")

        control_plane_endpoint = None
        services = {}
        cluster_status = "Ready"
        
        try:
            cmd = ["kubectl", "cluster-info"]
            cluster_info_result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            cleaned_output = _strip_ansi_codes(cluster_info_result.stdout)
            for line in cleaned_output.splitlines():
                if "is running at" in line:
                    parts = line.split(" is running at ")
                    if len(parts) == 2:
                        service_name = parts[0].strip()
                        endpoint = parts[1].strip()
                        if "Kubernetes control plane" in service_name:
                            control_plane_endpoint = endpoint
                        else:
                            services[service_name] = endpoint
        except Exception as e:
            logger.warning(f"kubectl cluster-info failed, endpoints will be missing: {e}")
            cluster_status = "Unknown"

        platform = "Unknown"
        node_count = 0
        try:
            nodes = v1.list_node()
            if nodes.items:
                platform = nodes.items[0].status.node_info.os_image
            node_count = len(nodes.items)
        except Exception as e:
            logger.warning(f"Could not list nodes: {e}")

        try:
            health_cmd = ["kubectl", "get", "--raw", "/healthz"]
            health = subprocess.run(health_cmd, check=True, capture_output=True, text=True)
            if health.stdout.strip() != "ok":
                cluster_status = "Degraded"
        except Exception as e:
            logger.warning(f"Could not get /healthz, cluster status may be inaccurate: {e}")
            if cluster_status != "Unknown":
                cluster_status = "Unhealthy"
        
        # Use a generic result message
        result = "Cluster info retrieved successfully."
        
        return ClusterInfoResponse(
            result=result,
            kubernetes_version=k8s_version,
            platform=platform,
            node_count=node_count,
            control_plane_endpoint=control_plane_endpoint,
            core_services=services,
            cluster_status=cluster_status
        )
        
    except Exception as e:
        error_msg = f"Failed to get cluster information: {str(e)}"
        logger.error(error_msg)
        return ClusterInfoResponse(
            error=error_msg
        )



# -------rancher actions-------


def start_vm(vm_name: str, namespace: str = "default") -> VMResponse:
    """
    Start a Harvester VM via Rancher CLI.
    Equivalent to virtctl start but works anywhere Rancher CLI is logged in.

    Args:
        vm_name (str): The name of the VM to start.
        namespace (str, optional): The namespace of the VM. Defaults to "default".

    Returns:
        VMResponse: Result message indicating success or failure.
    """
    try:
        payload = _vm_patch_payload(True)
        _rancher_kubectl(namespace, ["patch", "vm", vm_name,
                                     "--type", "merge",
                                     "-p", payload])
        return VMResponse(
            result=f"VM {vm_name} started",
            vm_name=vm_name,
            namespace=namespace,
            status="Running",
            ready=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(e.stderr)
        return VMResponse(
            error=e.stderr,
            vm_name=vm_name,
            namespace=namespace
        )

def stop_vm(vm_name: str, namespace: str = "default") -> VMResponse:
    """
    Gracefully stop a Harvester VM via Rancher CLI.

    Args:
        vm_name (str): The name of the VM to stop.
        namespace (str, optional): The namespace of the VM. Defaults to "default".

    Returns:
        VMResponse: Result message indicating success or failure.
    """
    try:
        payload = _vm_patch_payload(False)
        _rancher_kubectl(namespace, ["patch", "vm", vm_name,
                                     "--type", "merge",
                                     "-p", payload])
        return VMResponse(
            result=f"VM {vm_name} stopped",
            vm_name=vm_name,
            namespace=namespace,
            status="Stopped",
            ready=False
        )
    except subprocess.CalledProcessError as e:
        logger.error(e.stderr)
        return VMResponse(
            error=e.stderr,
            vm_name=vm_name,
            namespace=namespace
        )

@action(is_consequential=True)
def power_vm_rancher(vm_name: str,
                     namespace: str = "default",
                     running: bool = True) -> VMResponse:
    """
    Unified wrapper around start_vm / stop_vm choosing by flag.

    Args:
        vm_name (str): The name of the VM to operate on.
        namespace (str, optional): The namespace of the VM. Defaults to "default".
        running (bool, optional): If True, start the VM; if False, stop the VM. Defaults to True.

    Returns:
        VMResponse: Result message indicating success or failure.
    """
    return start_vm(vm_name, namespace) if running else stop_vm(vm_name, namespace)



# Global variable to store the current Rancher context (project ID string)
_CURRENT_RANCHER_CONTEXT = None

@action(is_consequential=True)
def set_rancher_context(project_id_or_name: str) -> RancherResponseSet:
    """
    Set the Rancher context persistently for all Rancher CLI operations.

    If the user provides a name (e.g., "vision") instead of a project_id (e.g., "c-xxxx:p-yyyy"),
    this function will always list all Rancher contexts, search for a matching name (case-insensitive),
    and use its project_id. If the name is not found, it will return an error and show available context names.
    Do not assume the user is providing a project_id unless it contains a colon (":").

    Example usage:
        set_rancher_context("vision")
        # This will search for a context named "vision" and set its project_id as the context.

        set_rancher_context("c-xxxx:p-yyyy")
        # This will set the context directly if a project_id is provided.

    Args:
        project_id_or_name (str): The Rancher project ID (e.g., "c-xxxx:p-yyyy") or the context name (e.g., "vision").
            If a name is provided, it will be resolved to the corresponding project ID.

    Returns:
        RancherResponseSet: Response indicating the result of setting the Rancher context.
    """
    global _CURRENT_RANCHER_CONTEXT
    # If the input looks like a project_id (contains a colon), use it directly, else search by name
    if ":" not in project_id_or_name:
        # List all contexts and try to match by name (case-insensitive)
        try:
            contexts_resp = list_rancher_contexts()
            if hasattr(contexts_resp, "contexts"):
                contexts = contexts_resp.contexts
            else:
                return RancherResponseSet(
                    result=None,
                    error="Could not retrieve Rancher contexts.",
                    context=None
                )
            match = None
            for ctx in contexts:
                if ctx["name"].lower() == project_id_or_name.lower():
                    match = ctx
                    break
            if not match:
                available = ", ".join([ctx["name"] for ctx in contexts])
                return RancherResponseSet(
                    result=None,
                    error=f"No Rancher context found with name '{project_id_or_name}'. Available: {available}",
                    context=None
                )
            project_id = match["project_id"]
        except Exception as e:
            return RancherResponseSet(
                result=None,
                error=f"Failed to list Rancher contexts: {e}",
                context=None
            )
    else:
        project_id = project_id_or_name
    _CURRENT_RANCHER_CONTEXT = project_id
    # Persist context to file
    context_file = os.path.expanduser("~/.rancher/selected_context")
    try:
        os.makedirs(os.path.dirname(context_file), exist_ok=True)
        with open(context_file, "w") as f:
            f.write(project_id.strip())
    except Exception as e:
        return RancherResponseSet(
            result=None,
            error=f"Failed to persist Rancher context: {e}",
            context=project_id
        )
    return RancherResponseSet(
        result=f"Rancher context set to: {project_id}",
        error=None,
        context=project_id
    )

def get_rancher_context() -> str:
    """
    Get the current Rancher context. If not set, try to load from file, else raise error.
    """
    global _CURRENT_RANCHER_CONTEXT
    if _CURRENT_RANCHER_CONTEXT:
        return _CURRENT_RANCHER_CONTEXT
    context_file = os.path.expanduser("~/.rancher/selected_context")
    if os.path.exists(context_file):
        with open(context_file, "r") as f:
            context = f.read().strip()
            if context:
                _CURRENT_RANCHER_CONTEXT = context
                return context
    raise RuntimeError("No Rancher context set. Use set_rancher_context(context) to set it.")

def _get_rancher_auth_args(context: Optional[str] = None) -> list[str]:
    """
    Get Rancher authentication arguments from environment variables, using the provided context or the global one.
    Returns command arguments for rancher login, ready to use.
    """
    rancher_url = os.getenv("RANCHER_URL")
    rancher_token = os.getenv("RANCHER_TOKEN")
    rancher_context = context if context else get_rancher_context()
    if not rancher_url or not rancher_token or not rancher_context:
        raise RuntimeError("Missing required environment variables: RANCHER_URL, RANCHER_TOKEN, and RANCHER_CONTEXT. Set these in your .env file for Docker container deployment. Example: RANCHER_CONTEXT=c-h9sm2:p-nbpv8")
    return ["login", rancher_url, "--token", rancher_token, "--context", rancher_context]

def _rancher_kubectl(namespace: str, kubectl_args: list[str]) -> str:
    """
    Execute `rancher kubectl` with environment-based authentication.
    Authenticates fresh for each command - ideal for containerized deployments.
    Raises subprocess.CalledProcessError on non-zero exit.
    """
    try:
        # Get auth args from environment
        auth_args = _get_rancher_auth_args()
        
        # First, authenticate (output redirected to avoid noise)
        login_cmd = ["rancher"] + auth_args
        subprocess.run(login_cmd, check=True, capture_output=True, text=True)
        
        # Then execute the kubectl command
        cmd = ["rancher", "kubectl", "-n", namespace] + kubectl_args
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Rancher command failed: {e.stderr}")
        raise RuntimeError(f"Rancher operation failed: {e.stderr}")

def _vm_patch_payload(start: bool) -> str:
    """
    Use runStrategy to control VM power state, removing the deprecated 'running' field.
    Returns a JSON string safe for `kubectl -p`.
    """
    strategy = "RerunOnFailure" if start else "Halted"
    # Set running to null to remove it from the spec, preventing the 'mutually-exclusive' error.
    payload = {
        "spec": {
            "running": None,
            "runStrategy": strategy
        }
    }
    return json.dumps(payload) 

@action(is_consequential=False)
def list_vms(namespace: str = "default") -> VMListResponse:
    """
    List all virtual machines (VMs) in the specified namespace using Rancher kubectl.

    This action retrieves a list of Harvester or KubeVirt VMs, not Kubernetes pods or namespaces.
    It shows the VM name, status (Running/Stopped), and readiness.


    Hint: To list VMs for a different Rancher context (project/cluster), use set_rancher_context(project_id) before calling this function.
    Example: If you want to list VMs for the context named "arc-reactor", first find its project_id using list_rancher_contexts(), then call set_rancher_context(project_id) with the project_id for "arc-reactor", and finally call list_vms().

    Args:
        namespace (str, optional): The namespace to list VMs from. Defaults to "default".

    Returns:
        VMListResponse: A formatted list of VMs with their status.
    """
    try:
        output = _rancher_kubectl(namespace, ["get", "vms"])
        lines = output.splitlines()
        if len(lines) < 2:
            return VMListResponse(
                result="No VMs found.",
                namespace=namespace,
                vms=[]
            )
            
        header = lines[0].split()
        name_idx = header.index("NAME") if "NAME" in header else 0
        status_idx = header.index("STATUS") if "STATUS" in header else 2
        ready_idx = header.index("READY") if "READY" in header else 3
        vm_list = []
        
        for line in lines[1:]:
            cols = line.split()
            if len(cols) > max(name_idx, status_idx, ready_idx):
                status = cols[status_idx]
                ready = cols[ready_idx]
                vm_list.append({
                    "name": cols[name_idx],
                    "status": status,
                    "ready": ready == "True"
                })
                
        if not vm_list:
            return VMListResponse(
                result="No VMs found.",
                namespace=namespace,
                vms=[]
            )
            
        result = "Virtual Machines\n\n"
        for vm in vm_list:
            status_text = "Running" if vm["ready"] and vm["status"] == "Running" else "Stopped" if vm["status"] == "Stopped" else "Unknown"
            result += f"- {vm['name']} | {status_text} | Ready: {vm['ready']}\n"
            
        return VMListResponse(
            result=result,
            namespace=namespace,
            vms=vm_list
        )
    except Exception as e:
        error_msg = f"Failed to list VMs: {str(e)}"
        return VMListResponse(
            error=error_msg,
            namespace=namespace,
            vms=[]
        )

@action(is_consequential=False)
def list_rancher_contexts() -> RancherContextResponse:
    """
    List all available Rancher contexts (project IDs) by parsing the Rancher CLI config file.

    Returns:
        RancherContextResponse: A list of Rancher contexts and their details.
    """
    try:
        config_path = os.path.expanduser("~/.rancher/cli2.json")
        
        if not os.path.exists(config_path):
            return RancherContextResponse(
                error=f"Rancher config file not found at {config_path}",
                contexts=[]
            )

        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        servers = config_data.get("Servers", {})
        current_server = config_data.get("CurrentServer")
        contexts = []
        
        for server_name, server_data in servers.items():
            project_id = server_data.get("project")
            if project_id:
                contexts.append({
                    "name": server_name,
                    "is_current": server_name == current_server,
                    "project_id": project_id
                })
                
        result = "Rancher Contexts:\n"
        for ctx in contexts:
            current_marker = "(current)" if ctx["is_current"] else ""
            result += f"- {ctx['name']} {current_marker}\n"
            result += f"  Project ID: {ctx['project_id']}\n"
            
        return RancherContextResponse(
            result=result,
            contexts=contexts
        )
    except Exception as e:
        error_msg = f"Failed to list Rancher contexts from config file: {str(e)}"
        return RancherContextResponse(
            error=error_msg,
            contexts=[]
        )

@action(is_consequential=True)
def download_cluster_kubeconfig(cluster_name: str, kubeconfig_path: str = "~/.kube/config") -> KubeConfigResponse:
    """
    Download the Kubeconfig for a Harvester cluster from Rancher using the Rancher CLI and append it to the specified local file. Sets the module-level kubeconfig path for future use.

    Args:
        cluster_name (str): The name of the Harvester cluster to download the kubeconfig for.
        kubeconfig_path (str, optional): The local file path to append the kubeconfig to. Defaults to "~/.kube/config".

    Returns:
        KubeConfigResponse: Result message indicating success or failure.
    """
    global _KUBECONFIG_PATH
    try:
        # Authenticate with Rancher using credentials from environment variables.
        auth_args = _get_rancher_auth_args()
        login_cmd = ["rancher"] + auth_args
        subprocess.run(login_cmd, check=True, capture_output=True, text=True, timeout=60)

        # Command to generate the kubeconfig for the specified cluster.
        kubeconfig_cmd = ["rancher", "clusters", "kubeconfig", cluster_name]
        result = subprocess.run(kubeconfig_cmd, check=True, capture_output=True, text=True, timeout=60)
        kubeconfig_content = result.stdout

        # Expand user path (e.g., '~') and create directory if it doesn't exist.
        expanded_path = os.path.expanduser(kubeconfig_path)
        os.makedirs(os.path.dirname(expanded_path), exist_ok=True)

        # Append the kubeconfig content to the specified file.
        with open(expanded_path, "a") as f:
            f.write("\n" + kubeconfig_content)
        
        # Set module-level kubeconfig path for all future k8s API calls
        _KUBECONFIG_PATH = expanded_path
        logger.info(f"Set _KUBECONFIG_PATH to '{expanded_path}' for subsequent Kubernetes API calls.")
        logger.info(f"Kubeconfig for cluster '{cluster_name}' successfully appended to '{expanded_path}'")
        # Return a clean, human-readable message
        return KubeConfigResponse(
            result="SUCCESS: KUBECONFIG DOWNLOADED",
            cluster_name=cluster_name,
            kubeconfig_path=expanded_path
        )

    except subprocess.CalledProcessError as e:
        # Handle errors from the Rancher CLI command.
        error_message = f"Failed to download kubeconfig for cluster '{cluster_name}': {e.stderr}"
        logger.error(error_message)
        return KubeConfigResponse(error=error_message)
    except Exception as e:
        # Handle other potential errors (e.g., file permissions).
        error_message = f"An unexpected error occurred while downloading kubeconfig for '{cluster_name}': {str(e)}"
        logger.error(error_message)
        return KubeConfigResponse(error=error_message)

@action(is_consequential=True)
def kube_control_action(command: str, namespace: str) -> KubeControlResponse:
    """
    Executes an arbitrary kubectl command using Rancher context.

    Args:
        command (str): The kubectl command to execute (e.g., "get pods").
        namespace (str, optional): The namespace to use. Defaults to "default".

    Returns:
        KubeControlResponse: The result of the command execution.
    """
    try:
        args = command.split()
        # Remove any namespace args from the command string to avoid conflicts
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                del args[i:i+2]
                continue
            elif args[i].startswith("--namespace="):
                del args[i]
                continue
            elif args[i] == "--namespace" and i + 1 < len(args):
                del args[i:i+2]
                continue
            i += 1
        try:
            output = _rancher_kubectl(namespace, args)
            return KubeControlResponse(
                result=output,
                error=None,
                returncode=0
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(error_msg)
            return KubeControlResponse(
                result=None,
                error=error_msg,
                returncode=1
            )
    except Exception as e:
        error_msg = str(e)
        logger.error(error_msg)
        return KubeControlResponse(
            result=None,
            error=error_msg,
            returncode=1
        )