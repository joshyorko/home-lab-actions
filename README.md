# [![Open in DevPod!](https://devpod.sh/assets/open-in-devpod.svg)](https://devpod.sh/open#https://github.com/joshyorko/home-lab-actions)
# Home Lab Actions

AI Actions for managing Kubernetes clusters and Harvester VMs in your home lab environment.

## Features

### Kubernetes Actions
- List pods in any namespace (`list_pods`)
- Get logs from a specific pod (`get_pod_logs`)
- List all namespaces in the cluster (`list_namespaces`)
- List deployments in any namespace (`list_deployments`)
- Get cluster information (version, platform, node count, endpoints, health) (`get_cluster_info`)
- Execute arbitrary kubectl commands using Rancher context (`kube_control_action`)

### Harvester VM Control (via Rancher CLI)
- List all virtual machines (VMs) in a namespace (`list_vms`)
- Start a VM (`start_vm`)
- Stop a VM (`stop_vm`)
- Unified power control with boolean toggle (`power_vm_rancher`)
- Set and persist Rancher context for CLI operations (`set_rancher_context`)
- Get the current Rancher context (`get_rancher_context`)
- List all Rancher contexts (project IDs) (`list_rancher_contexts`)
- Download kubeconfig for a Harvester cluster (`download_cluster_kubeconfig`)
- Works anywhere Rancher CLI is logged in (no kubeconfig juggling)

### SSH Actions
- Execute commands on remote systems via SSH (Vision system)
- Supports password and key-based authentication
- Optional TLS certificate support for advanced workflows

## Prerequisites

### For Kubernetes Actions
- Valid kubeconfig file or in-cluster configuration
- Appropriate RBAC permissions for cluster resources

### For Harvester VM Actions
These actions require Rancher CLI ≥ v2.11 logged into a project that has Harvester VMs.

Log in once with:
```bash
rancher login $RANCHER_URL --token $RANCHER_TOKEN --context $RANCHER_PROJECT --skip-verify
```

Example interactive project selection:
```bash
rancher login https://rancher.example.com --token token-xxxxx --skip-verify
# Select the project containing your Harvester VMs from the interactive list
```

## Usage Examples

### VM Control
```python
# Start a VM
start_vm("coolify")  # VM coolify started

# Stop a VM
stop_vm("coolify")   # VM coolify stopped

# Toggle VM state with boolean
power_vm_rancher("my-vm", namespace="harvester-public", running=True)   # Start
power_vm_rancher("my-vm", namespace="harvester-public", running=False)  # Stop
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