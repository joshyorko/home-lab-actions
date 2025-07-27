
from typing import Optional
import os
import shutil
import subprocess
import json
import logging
from .models import VMResponse
from dotenv import load_dotenv
# Explicitly load the .env file from the specified path
load_dotenv()

logger = logging.getLogger(__name__)



class RancherTools:
    def __init__(self):
        self._current_context = None
        self.logger = logging.getLogger("RancherTools")

    def _require_bin(self, name: str):
        if not shutil.which(name):
            raise RuntimeError(f"Required binary '{name}' not found in PATH")

    def ensure_env(self):
        url = os.getenv("RANCHER_URL")
        token = os.getenv("RANCHER_TOKEN")
        if not url or not token:
            raise RuntimeError("RANCHER_URL and RANCHER_TOKEN are required")
        return url, token

    def _augment_login_flags(self, cmd: list[str]) -> list[str]:
        insecure = os.getenv("RANCHER_INSECURE", "").lower() in ("1", "true", "yes")
        cacerts = os.getenv("RANCHER_CACERTS")
        if insecure:
            cmd.append("--insecure")
        if cacerts:
            cmd += ["--cacerts", cacerts]
        return cmd

    def _login_cmd(self, url: str, token: str, context: Optional[str] = None) -> list[str]:
        cmd = ["rancher", "login", url, "--token", token]
        if context:
            cmd += ["--context", context]
        return self._augment_login_flags(cmd)

    def rancher_login_no_context(self):
        self._require_bin("rancher")
        url, token = self.ensure_env()
        subprocess.run(
            self._login_cmd(url, token),
            check=True, capture_output=True, text=True, timeout=60
        )

    def is_cli_initialized(self) -> bool:
        return os.path.exists(os.path.expanduser("~/.rancher/cli2.json"))

    def ensure_rancher_login(self):
        self._require_bin("rancher")
        if not self.is_cli_initialized():
            self.rancher_login_no_context()

    def resolve_context(self, name_or_id: str) -> str:
        if ":" in name_or_id:
            return name_or_id.strip()
        self.ensure_rancher_login()
        cfg = os.path.expanduser("~/.rancher/cli2.json")
        with open(cfg) as f:
            data = json.load(f)
        servers = data.get("Servers", {})
        preferred = [data.get("CurrentServer")] if data.get("CurrentServer") else []
        for server_name in preferred + list(servers.keys()):
            s = servers.get(server_name)
            if not s:
                continue
            proj = s.get("project")
            if proj and server_name.lower() == name_or_id.lower():
                return proj
        for server_name, s in servers.items():
            if s.get("project") and name_or_id.lower() in server_name.lower():
                return s["project"]
        raise RuntimeError(f"Context '{name_or_id}' not found. Run an interactive 'rancher context switch' to inspect available items.")

    def select_context(self, project_id: str):
        self._require_bin("rancher")
        url, token = self.ensure_env()
        subprocess.run(
            self._login_cmd(url, token, context=project_id),
            check=True, capture_output=True, text=True, timeout=60
        )
        path = os.path.expanduser("~/.rancher/selected_context")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            f.write(project_id.strip())
        os.replace(tmp, path)
        self._current_context = project_id.strip()

    def _current_context_from_file(self) -> Optional[str]:
        f = os.path.expanduser("~/.rancher/selected_context")
        if os.path.exists(f):
            with open(f, "r") as fh:
                return fh.read().strip() or None
        return None

    def _rancher_kubectl(self, namespace: str, kubectl_args: list[str], context: Optional[str]=None) -> str:
        self.ensure_rancher_login()
        ctx = context or self._current_context_from_file()
        url, token = self.ensure_env()
        subprocess.run(self._login_cmd(url, token, context=ctx),
                       check=True, capture_output=True, text=True)
        cmd = ["rancher", "kubectl", "-n", namespace] + kubectl_args
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def get_rancher_context(self) -> str:
        """
        Get the current Rancher context. If not set, try to load from file, else raise error.
        """
        if self._current_context:
            return self._current_context
        context_file = os.path.expanduser("~/.rancher/selected_context")
        if os.path.exists(context_file):
            with open(context_file, "r") as f:
                context = f.read().strip()
                if context:
                    self._current_context = context
                    return context
        raise RuntimeError("No Rancher context set. Use set_rancher_context(context) to set it.")

    def _vm_patch_payload(self, start: bool) -> str:
        strategy = "RerunOnFailure" if start else "Halted"
        payload = {
            "spec": {
                "running": None,
                "runStrategy": strategy
            }
        }
        return json.dumps(payload)

    def start_vm(self, vm_name: str, namespace: str = "default") -> VMResponse:
        try:
            payload = self._vm_patch_payload(True)
            self._rancher_kubectl(namespace, ["patch", "vm", vm_name,
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
            self.logger.error(e.stderr)
            return VMResponse(
                error=e.stderr,
                vm_name=vm_name,
                namespace=namespace
            )

    def stop_vm(self, vm_name: str, namespace: str = "default") -> VMResponse:
        try:
            payload = self._vm_patch_payload(False)
            self._rancher_kubectl(namespace, ["patch", "vm", vm_name,
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
            self.logger.error(e.stderr)
            return VMResponse(
                error=e.stderr,
                vm_name=vm_name,
                namespace=namespace
            )
