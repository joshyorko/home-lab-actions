"""
Response models for Kubernetes actions.
"""
from sema4ai.actions import Response
from typing import List, Optional

class PodResponse(Response[str]):
    namespace: str | None = None
    pod_count: int = 0
    pods: List[dict] = []

class PodLogResponse(Response[str]):
    pod_name: str | None = None
    namespace: str | None = None
    tail_lines: int = 50
    logs: str | None = None





class NamespaceResponse(Response[str]):
    total_namespaces: int = 0
    namespaces: List[str] = []

class DeploymentListResponse(Response[str]):
    namespace: str | None = None
    deployment_count: int = 0
    deployments: List[dict] = []

class ClusterInfoResponse(Response[str]):
    kubernetes_version: str | None = None
    platform: str | None = None
    node_count: int = 0
    control_plane_endpoint: str | None = None
    core_services: dict[str, str] = {}  # service_name -> endpoint URL
    cluster_status: str = "Unknown"     # Overall cluster health status

class PodDeleteResponse(Response[str]):
    pod_name: str | None = None
    namespace: str | None = None

class VMResponse(Response[str]):
    vm_name: str | None = None
    status: str | None = None
    ready: bool = False
    namespace: str | None = None

class VMListResponse(Response[str]):
    namespace: str | None = None
    vms: List[dict] = []


class RancherContextResponse(Response[str]):
    contexts: List[dict] = []

class RancherResponseSet(Response[str]):
    context: Optional[str] = None

class KubeConfigResponse(Response[str]):
    cluster_name: str | None = None
    kubeconfig_path: str | None = None

class KubeControlResponse(Response[str]):
    # 'result' (from Response) will be used for stdout
    # 'error' (from Response) will be used for stderr
    returncode: int | None = None
