import re
import sys
import subprocess
from pathlib import Path

# ------------------------------
# Arguments et fichiers
# ------------------------------
bump = sys.argv[1] if len(sys.argv) > 1 else "patch"
version_file = Path(__file__).parent / "pyverse2d" / "_version.py"
pyproject_file = Path(__file__).parent / "pyproject.toml"

# ------------------------------
# Incrémentation de  _version.py
# ------------------------------
with open(version_file, "r") as f:
    content = f.read()

match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
if not match:
    raise ValueError("Version non trouvée dans _version.py")

major, minor, patch_num = map(int, match.groups())

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
    raise ValueError("Argument invalide, choisir patch/minor/major")

new_version = f"{major}.{minor}.{patch_num}"

# Update de _version.py
new_content = re.sub(r'__version__\s*=\s*"\d+\.\d+\.\d+"',
                     f'__version__ = "{new_version}"', content)
with open(version_file, "w") as f:
    f.write(new_content)

print(f"[+] _version.py mis à jour → {new_version}")

# ------------------------------
# Mise à jour du pyproject.toml
# ------------------------------
with open(pyproject_file, "r") as f:
    pyproject_content = f.read()

pyproject_content = re.sub(r'version\s*=\s*"\d+\.\d+\.\d+"',
                           f'version = "{new_version}"', pyproject_content)

with open(pyproject_file, "w") as f:
    f.write(pyproject_content)

print(f"[+] pyproject.toml mis à jour → {new_version}")

# ------------------------------
# Nettoyage de dist/
# ------------------------------
dist_dir = Path(__file__).parent / "dist"
if dist_dir.exists():
    for file in dist_dir.iterdir():
        file.unlink()
    print("[+] dist/ nettoyé")

# ------------------------------
# Build
# ------------------------------
subprocess.run(["python", "-m", "build"], check=True)
print("[+] Build terminé")

# ------------------------------
# Upload PyPI
# ------------------------------
subprocess.run(["python", "-m", "twine", "upload", "dist/*"], check=True)
print("[+] Upload PyPI terminé")

# ------------------------------
# Git commit & push
# ------------------------------
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", f"chore(version): bump to version {new_version}"])
subprocess.run(["git", "push", "origin", "main"])
print(f"[+] Version {new_version} commitée et pushée sur main")