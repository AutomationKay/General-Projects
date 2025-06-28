# tests/test_pipeline.py

import subprocess
import os
import pytest

def test_run_all_script_executes_successfully():
    result = subprocess.run(["python", "src/run_all.py"], capture_output=True, text=True)

    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    assert result.returncode == 0, "run_all.py did not exit cleanly"
    assert "Pipeline completed" in result.stdout or "Completed" in result.stdout, \
        "Pipeline did not indicate success in stdout"
