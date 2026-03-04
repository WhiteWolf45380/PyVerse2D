# _sync_version_simple.py
version_file = "engine/_version.py"
toml_file = "pyproject.toml"

# lire la version
with open(version_file) as f:
    code = f.read()
exec(code)

# lire le pyproject.toml
with open(toml_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# remplacer la ligne commençant par "version ="
for i, line in enumerate(lines):
    if line.strip().startswith("version ="):
        lines[i] = f'version = "{__version__}"\n'
        break

# écrire à nouveau
with open(toml_file, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"pyproject.toml mis à jour avec la version {__version__}")