import io
import json
import logging
import re
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Dict

logger = logging.getLogger(__name__)

ALLOWED_BUILTINS = {
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
    "frozenset", "int", "isinstance", "len", "list", "map", "max", "min",
    "print", "range", "repr", "reversed", "round", "set", "slice", "sorted",
    "str", "sum", "tuple", "type", "zip",
}

BLOCKED_MODULES = {
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "http", "urllib", "ftplib", "smtplib",
}

_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE
)


class Sandbox:
    def __init__(self, timeout: int = 30):
        self._timeout = timeout

    def execute(self, code: str, context_vars: Dict[str, Any] = None) -> Dict[str, Any]:
        blocked = set()
        for match in _IMPORT_RE.finditer(code):
            mod = match.group(1)
            if mod in BLOCKED_MODULES:
                blocked.add(mod)
        if blocked:
            logger.warning("Blocked import attempt: %s", ", ".join(sorted(blocked)))
            return {
                "stdout": "",
                "stderr": "",
                "error": f"Blocked imports: {', '.join(sorted(blocked))}",
                "variables": {},
            }

        builtins_dict = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__
        safe_builtins = {name: builtins_dict[name] for name in ALLOWED_BUILTINS}

        def _run():
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            local_vars = dict(context_vars or {})
            result = {"stdout": "", "stderr": "", "error": None, "variables": {}}
            try:
                exec(
                    code,
                    {"__builtins__": safe_builtins, "pd": __import__("pandas"), "np": __import__("numpy")},
                    local_vars,
                )
                result["stdout"] = sys.stdout.getvalue()
                result["stderr"] = sys.stderr.getvalue()
                for k, v in local_vars.items():
                    if not k.startswith("_"):
                        try:
                            json.dumps(v)
                            result["variables"][k] = v
                        except (TypeError, ValueError):
                            result["variables"][k] = str(v)
            except Exception:
                result["error"] = traceback.format_exc()
                result["stderr"] = sys.stderr.getvalue()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            return result

        logger.info("Executing sandboxed code (%d chars, timeout=%ds)", len(code), self._timeout)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            try:
                return future.result(timeout=self._timeout)
            except TimeoutError:
                logger.warning("Sandbox execution timed out after %ds", self._timeout)
                return {
                    "stdout": "",
                    "stderr": "",
                    "error": f"Execution timed out after {self._timeout} seconds",
                    "variables": {},
                }
