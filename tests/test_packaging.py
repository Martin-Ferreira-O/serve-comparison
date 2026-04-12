import os
import subprocess
import sys
from pathlib import Path


def test_dockerfile_copies_app_before_install():
    dockerfile = Path(__file__).resolve().parents[1] / "Dockerfile"
    lines = dockerfile.read_text(encoding="utf-8").splitlines()

    copy_app_index = lines.index("COPY app ./app")
    install_index = lines.index("RUN pip install --no-cache-dir .")

    assert copy_app_index < install_index


def test_installed_package_can_start_app_and_render_dashboard(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    install_target = tmp_path / "site"
    sqlite_path = tmp_path / "comparison.sqlite3"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            ".",
            "--target",
            str(install_target),
        ],
        check=True,
        cwd=repo_root,
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(install_target)
    env["COMPARISON_SQLITE_PATH"] = str(sqlite_path)

    subprocess.run(
        [
            sys.executable,
            "-c",
            "from fastapi.testclient import TestClient; "
            "from app.main import create_app; "
            "client = TestClient(create_app()); "
            "response = client.get('/'); "
            "assert response.status_code == 200; "
            "assert 'comparison.css' in response.text; "
            "assert 'Dashboard de comparacion' in response.text",
        ],
        check=True,
        env=env,
        cwd=tmp_path,
    )
