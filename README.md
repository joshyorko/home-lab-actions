# [![Open in DevPod!](https://devpod.sh/assets/open-in-devpod.svg)](https://devpod.sh/open#https://github.com/joshyorko/home-lab-actions)
# Home Lab Actions

AI Actions for managing Kubernetes clusters and executing SSH commands in your home lab environment.

## Available Actions

### Kubernetes Actions
- List pods in any namespace (`list_pods`)
- Get logs from a specific pod (`get_pod_logs`)
- List all namespaces in the cluster (`list_namespaces`)
- List deployments in any namespace (`list_deployments`)
- Get cluster information (version, platform, node count, endpoints, health) (`get_cluster_info`)

### SSH Actions
- Execute commands on remote systems via SSH (Vision system)
- Supports password and key-based authentication

## Prerequisites

### For Kubernetes Actions
- Valid kubeconfig file or in-cluster configuration
- Appropriate RBAC permissions for cluster resources

### For SSH Actions
- Set environment variables for Vision system connection: `VISION_IP`, `VISION_USERNAME`, `PASSWORD` or `SSH_KEY`

## Usage Examples

### Kubernetes
```python
# List pods in a namespace
list_pods("default")

# Get logs from a pod
get_pod_logs("pod-name", namespace="default", tail_lines=50)

# List namespaces
list_namespaces()

# List deployments
list_deployments("default")

# Get cluster info
get_cluster_info()
```

### SSH Command Execution
```python
execute_command_on_vision("ls -la")  # Runs command on Vision system via SSH
```

## Extensibility

You can leverage the whole Python ecosystem when creating actions. Sema4.ai provides a [bunch of libraries](https://pypi.org/search/?q=robocorp-); you can make your own.

Check [Action Server](https://github.com/Sema4AI/actions/tree/master/action_server/docs) and [Actions](https://github.com/Sema4AI/actions/tree/master/actions/docs) docs for more information.

---

### Contributors

![Contributors](https://contrib.nn.ci/api?repo=joshyorko/home-lab-actions)