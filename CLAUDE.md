# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Lab Actions is an AI-driven action server for managing Kubernetes clusters and executing SSH commands in a home lab environment. The project provides Python-based actions for:
- Kubernetes/Rancher operations (list pods, get logs, manage deployments, etc.)
- Virtual machine management via Rancher (list, start, stop VMs)
- SSH command execution on remote systems

## Build & Run Commands

### Docker Workflow

```bash
# Build and run the container
docker-compose build
docker-compose up -d

# Access the API at http://localhost:4000 or https://localhost:443
```

### Development Workflow

```bash
# Setup Python environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt  # Requirements are derived from package.yaml

# Import actions to local action server
action-server import --datadir=/path/to/datadir

# Start the action server for development
action-server start --datadir=/path/to/datadir --actions-sync=false
```

### Environment Setup

Required environment variables for different features:
- For Rancher: `RANCHER_URL`, `RANCHER_TOKEN`
- For SSH: `VISION_IP`, `VISION_USERNAME`, and either `PASSWORD` or `SSH_KEY`

## Architecture

### Key Components

1. **Action Server:** Processes requests and exposes actions via HTTP endpoints
   - Configured via supervisord (`config/supervisord.conf`)
   - API exposed through nginx reverse proxy (`config/nginx.conf`)

2. **Python Actions:**
   - `src/rancher_actions/k8s-actions.py`: Kubernetes-related actions
   - `src/rancher_actions/tools.py`: Core functionality for Rancher CLI operations
   - `src/home_lab_actions/ssh_actions.py`: SSH command execution

3. **Data Models:**
   - `src/rancher_actions/models.py`: Response models for all actions

### Architectural Patterns

- **Action-Oriented Design:** Each function in Python files is exposed as an HTTP endpoint
- **Separation of Concerns:** Kubernetes and SSH actions are kept in separate modules
- **Tools & Utilities Pattern:** Common functionality abstracted into `RancherTools` class

## Key Files & Directories

- `src/rancher_actions/k8s-actions.py`: Main Kubernetes/Rancher actions
- `src/rancher_actions/tools.py`: Rancher CLI interface utilities
- `src/home_lab_actions/ssh_actions.py`: SSH actions
- `config/supervisord.conf`: Process management configuration
- `config/nginx.conf`: HTTP/HTTPS routing configuration
- `Dockerfile`: Container definition for action server
- `docker-compose.yml`: Service orchestration
- `package.yaml`: Dependencies and packaging information

## Common Development Tasks

### Adding New Actions

1. Create functions in appropriate module files (`k8s-actions.py`, `ssh_actions.py`)
2. Add appropriate `@action` decorator from `sema4ai.actions`
3. Define response model in `models.py` if needed
4. Import action server with `action-server import`

### Testing Actions

Actions can be tested:
1. Directly by importing and calling functions
2. Via HTTP requests to the action server endpoints
3. Through the action server web UI

### Service Management

- Services are orchestrated using supervisord
- Both nginx and action-server run as foreground processes
- Configuration is in `config/supervisord.conf`

## Important Notes

- The system uses Rancher CLI for Kubernetes operations
- Authentication is handled via environment variables
- The project doesn't have formal testing infrastructure
- `~/.kube/config` is used for Kubernetes configuration
- `~/.rancher/cli2.json` is used for Rancher configuration