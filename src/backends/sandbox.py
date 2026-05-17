import json
import subprocess


class SandboxedToolExecutor:
    def __init__(self, tools: dict[str, str], image: str = "python:3.12-slim"):
        self._tools = tools
        self._image = image

    def __call__(self, tool_name: str, args: dict) -> str:
        snippet = self._tools.get(tool_name)
        if snippet is None:
            return f"[no sandbox handler for '{tool_name}']"

        args_json = json.dumps(args)
        script = f"import json, sys; args = json.loads({args_json!r})\n{snippet}"

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", "none",
                "--read-only",
                self._image,
                "python3", "-c", script,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Sandbox exited {result.returncode}: {result.stderr.strip()}")

        return result.stdout
