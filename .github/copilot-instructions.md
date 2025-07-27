# Copilot Instructions for AI Coding Agents

## Project Overview
This repository provides AI-driven actions for managing Kubernetes clusters and executing SSH commands in a home lab environment. The main logic is organized under `src/`:
- `src/rancher_actions/`: Kubernetes-related actions (pod/deployment/namespace management, cluster info)
- `src/home_lab_actions/`: SSH command execution on remote systems (Vision system)

## Service Orchestration & Runtime
- **nginx reverse proxy** (`config/nginx.conf`):
  - All HTTP(S) traffic is routed through nginx, which proxies requests to the internal action server (`localhost:8087`).
  - SSL is enforced using `combined-tls.crt` and `tls.key`.
  - Key endpoints:
    - `/openapi.json` → `/api/` → `/` all proxy to the action server.
- **Process management** (`config/supervisord.conf`):
  - `supervisord` runs both nginx and the action server as foreground processes.
  - Action server is started with SSL, custom data directory, and disables action sync for local-only actions.
  - Logs are streamed to stdout/stderr for container compatibility.

## How Config Relates to Python Actions
- The Python modules under `src/` implement the business logic for actions (Kubernetes, SSH, Rancher, etc.).
- The action server (see supervisord config) exposes these Python actions as HTTP endpoints, which nginx proxies securely.
- Environment variables (for SSH, Rancher, etc.) must be set before starting the action server for correct operation.

## Key Architectural Patterns
- **Action-Oriented Design:** Each action (e.g., `list_pods`, `get_pod_logs`, `execute_command_on_vision`) is implemented as a Python function, typically in `src/rancher_actions/k8s-actions.py` or `src/home_lab_actions/ssh_actions.py`.
- **Separation of Concerns:** Kubernetes and SSH actions are kept in separate modules. Cross-component communication is minimal and occurs via function calls.
- **Extensibility:** New actions can be added by defining Python functions in the appropriate module. Use the Python ecosystem and Sema4.ai libraries as needed.

## Developer Workflows
- **No explicit build step required.**
- **Run actions by importing and calling functions directly.**
- **Environment setup:**
  - For Kubernetes: Ensure a valid kubeconfig and RBAC permissions.
  - For SSH: Set `VISION_IP`, `VISION_USERNAME`, and either `PASSWORD` or `SSH_KEY` as environment variables.
- **Debugging:** Add print/log statements in action functions. There is no integrated test suite or build system detected.

## Running & Debugging Locally
- Start all services using supervisord (see `config/supervisord.conf`).
- Access the API via HTTPS on port 443 (nginx will proxy to the action server).
- Logs for both nginx and the action server are available in container stdout/stderr.

## Project-Specific Conventions
- **Function Naming:** Action functions use descriptive names (e.g., `list_pods`, `get_cluster_info`, `execute_command_on_vision`).
- **Configuration:**
  - Kubernetes config: `combined-tls.crt`, `tls.key`, `config/nginx.conf`, `config/supervisord.conf`
  - SSH config: Environment variables only
  - Kubernetes config: `combined-tls.crt`, `tls.key`, `config/nginx.conf`, `config/supervisord.conf`
  - nginx: SSL proxy for all API traffic
  - supervisord: orchestrates nginx and action server
  - SSH config: Environment variables only
- **Data Flow:** Inputs are passed as function arguments; outputs are returned directly or printed.
- **No custom decorators or metaprogramming detected.**

## Integration Points
- **Kubernetes:** Interacts via kubeconfig and Python Kubernetes client.
- **SSH:** Uses paramiko or similar libraries for remote command execution.
- **External Docs:** See [Action Server](https://github.com/Sema4AI/actions/tree/master/action_server/docs) and [Actions](https://github.com/Sema4AI/actions/tree/master/actions/docs) for advanced usage.

## Examples
```python
from src.rancher_actions.k8s-actions import list_pods, get_cluster_info
from src.home_lab_actions.ssh_actions import execute_command_on_vision

list_pods("default")
get_cluster_info()
execute_command_on_vision("ls -la")
```

## Service Startup Example
```shell
supervisord -c config/supervisord.conf
# Access API at https://localhost (nginx SSL proxy)
```

## Key Files & Directories
- `src/rancher_actions/k8s-actions.py`: Kubernetes actions
- `src/home_lab_actions/ssh_actions.py`: SSH actions
- `config/`: Service configuration files
- `README.md`: Usage and action documentation

- `config/nginx.conf`: nginx reverse proxy and SSL config
- `config/supervisord.conf`: process orchestration for nginx and action server

---
**If any conventions or workflows are unclear, please provide feedback so this document can be improved.**
