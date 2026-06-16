import io
import json
import logging
import multiprocessing
import queue
import re
import sys
import traceback
import types
from typing import Any, Dict

logger = logging.getLogger(__name__)

ALLOWED_BUILTINS = {
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
    "frozenset", "int", "isinstance", "len", "list", "map", "max", "min",
    "print", "range", "repr", "reversed", "round", "set", "slice", "sorted",
    "str", "sum", "tuple", "zip",
}

BLOCKED_MODULES = {
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "http", "urllib", "ftplib", "smtplib",
    "ctypes", "multiprocessing", "threading", "signal",
    "code", "codeop", "compileall", "py_compile",
    "builtins", "importlib", "pkgutil", "imp",
    "posix", "posixpath", "nt", "ntpath",
}

_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE
)

_IMPORT_CALL_RE = re.compile(
    r"__import__\s*\(['\"]([^'\"]+)['\"]", re.MULTILINE
)


def _make_safe_import():
    builtin_import = __import__

    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        top_module = name.split(".", 1)[0]
        if top_module in BLOCKED_MODULES:
            raise ImportError(f"Module '{name}' is blocked in sandbox")
        return builtin_import(name, globals, locals, fromlist, level)

    return safe_import


def _build_safe_globals():
    safe_builtins = types.SimpleNamespace()
    _real_builtins = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__
    for name in ALLOWED_BUILTINS:
        setattr(safe_builtins, name, _real_builtins.get(name))
    safe_builtins.__import__ = _make_safe_import()
    return {"__builtins__": safe_builtins, "pd": __import__("pandas"), "np": __import__("numpy")}


class Sandbox:
    def __init__(self, timeout: int = 30):
        self._timeout = timeout

    def execute(self, code: str, context_vars: Dict[str, Any] = None) -> Dict[str, Any]:
        blocked = set()
        for match in _IMPORT_RE.finditer(code):
            mod = match.group(1)
            if mod in BLOCKED_MODULES:
                blocked.add(mod)
        for match in _IMPORT_CALL_RE.finditer(code):
            mod = match.group(1).split(".", 1)[0]
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

        logger.info("Executing sandboxed code (%d chars, timeout=%ds)", len(code), self._timeout)
        mp_context = multiprocessing.get_context("spawn")
        output_queue = mp_context.Queue(maxsize=1)
        process = mp_context.Process(target=_run_sandboxed_code, args=(code, context_vars or {}, output_queue))
        process.start()
        process.join(self._timeout)

        if process.is_alive():
            process.terminate()
            process.join(1)
            logger.warning("Sandbox execution timed out after %ds", self._timeout)
            return {
                "stdout": "",
                "stderr": "",
                "error": f"Execution timed out after {self._timeout} seconds",
                "variables": {},
            }

        try:
            return output_queue.get_nowait()
        except queue.Empty:
            return {
                "stdout": "",
                "stderr": "",
                "error": "Sandbox process exited without returning a result",
                "variables": {},
            }


def _run_sandboxed_code(code: str, context_vars: Dict[str, Any], output_queue) -> None:
    safe_globals = _build_safe_globals()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    local_vars = dict(context_vars or {})
    result = {"stdout": "", "stderr": "", "error": None, "variables": {}}
    try:
        exec(code, safe_globals, local_vars)
        result["stdout"] = sys.stdout.getvalue()
        result["stderr"] = sys.stderr.getvalue()
        for k, v in local_vars.items():
            if not k.startswith("_"):
                try:
                    json.dumps(v)
                    result["variables"][k] = v
                except (TypeError, ValueError):
                    result["variables"][k] = repr(v)
    except Exception:
        result["error"] = traceback.format_exc()
        result["stderr"] = sys.stderr.getvalue()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    output_queue.put(result)
