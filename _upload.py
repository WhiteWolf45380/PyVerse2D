# ======================================== IMPORTS ========================================
import re
import sys
import subprocess
from pathlib import Path

# ======================================== ARGS ========================================
bump = sys.argv[1] if len(sys.argv) > 1 else "patch"

version_file = Path(__file__).parent / "pyverse2d" / "_version.py"
pyproject_file = Path(__file__).parent / "pyproject.toml"

# ======================================== VERSION READING ========================================
with open(version_file, "r") as f:
    content = f.read()

match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
if not match:
    raise ValueError("Version non trouvée dans _version.py")

major, minor, patch_num = map(int, match.groups())

# ======================================== BUMP VERSION ========================================
if bump == "patch":
    patch_num += 1
elif bump == "minor":
    minor += 1
    patch_num = 0
elif bump == "major":
    major += 1
    minor = 0
    patch_num = 0
else:
    raise ValueError("Argument invalide (patch / minor / major)")

new_version = f"{major}.{minor}.{patch_num}"

# ======================================== UPDATE VERSION ========================================
new_content = re.sub(
    r'__version__\s*=\s*"\d+\.\d+\.\d+"',
    f'__version__ = "{new_version}"',
    content
)

with open(version_file, "w") as f:
    f.write(new_content)

print(f"[+] _version.py → {new_version}")

# ======================================== UPDATE TOML ========================================
with open(pyproject_file, "r") as f:
    pyproject_content = f.read()

pyproject_content = re.sub(
    r'version\s*=\s*"\d+\.\d+\.\d+"',
    f'version = "{new_version}"',
    pyproject_content
)

with open(pyproject_file, "w") as f:
    f.write(pyproject_content)

print(f"[+] pyproject.toml → {new_version}")

# ======================================== GIT AUTOMATION ========================================
subprocess.run(["git", "add", "."])

subprocess.run([
    "git", "commit",
    "-m", f"chore: bump version to {new_version}"
])

subprocess.run(["git", "tag", f"v{new_version}"])

subprocess.run(["git", "push", "origin", "main"])
subprocess.run(["git", "push", "origin", f"v{new_version}"])

print(f"""
[✓] Version {new_version} publiée
""")