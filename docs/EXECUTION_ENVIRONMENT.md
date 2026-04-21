# Execution Environment Setup

This role can optionally attempt to install missing Python database drivers at runtime. That helps in writable execution environments, but the recommended approach for AWX and Ansible Tower is still to pre-install required packages in the execution environment image.

## Runtime Auto-Installation

Runtime package installation is controlled by these variables:

```yaml
execution_result_auto_install_packages: true
execution_result_package_install_method: "user"
```

Supported package mapping:

| Database | Python package |
|----------|----------------|
| PostgreSQL | `psycopg2-binary>=2.9.0` |
| MySQL | `PyMySQL>=1.0.0` |
| MongoDB | `pymongo>=4.0.0` |
| SQLite | none |

When enabled, the role:

1. Checks whether the required Python module is importable.
2. Attempts `python -m pip install --user <package>` when the module is missing.
3. Re-checks the import before running connectivity or database tasks.
4. Prints execution environment build instructions if installation fails.

This is useful for:

- Standalone Ansible control nodes with a writable home directory.
- Writable AWX execution environments where user site-packages are allowed.

This is not reliable for:

- Read-only containers.
- Execution environments without `pip`.
- Locked-down environments where `--user` installs are disabled.

## AWX / Ansible Tower

For AWX and Ansible Tower, pre-build the execution environment with required Python packages.

### Option 1: ansible-builder

Create `execution-environment.yml`:

```yaml
---
version: 3

images:
  base_image:
    name: quay.io/ansible/awx-ee:latest

dependencies:
  python: requirements.txt
  galaxy: requirements.yml
```

Create `requirements.txt`:

```text
psycopg2-binary>=2.9.0
PyMySQL>=1.0.0
pymongo>=4.0.0
```

Create `requirements.yml`:

```yaml
---
collections:
  - name: community.mysql
    version: ">=3.0.0"
  - name: community.mongodb
    version: ">=1.0.0"
  - name: community.general
    version: ">=6.0.0"
```

Notes:

- PostgreSQL does not require `community.postgresql` in this role.
- MySQL and MongoDB still require their Ansible collections because their database tasks use collection modules.

Build the image:

```bash
ansible-builder build -t my-custom-ee:latest
```

### Option 2: Dockerfile / Containerfile

```dockerfile
FROM quay.io/ansible/awx-ee:latest

RUN pip3 install --no-cache-dir \
    psycopg2-binary>=2.9.0 \
    PyMySQL>=1.0.0 \
    pymongo>=4.0.0

RUN ansible-galaxy collection install \
    community.mysql \
    community.mongodb \
    community.general
```

## Standalone Ansible

For standalone Ansible, either install into the system interpreter used by the role or point the role at a virtual environment.

### System Interpreter

```bash
python3 -m pip install psycopg2-binary
```

### Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install psycopg2-binary
```

Then configure the role:

```yaml
execution_result_python_interpreter: "/path/to/venv/bin/python"
```

## Recommended Settings

### AWX / Tower

```yaml
execution_result_python_interpreter: "python3"
execution_result_auto_install_packages: true
execution_result_package_install_method: "user"
```

### Standalone Ansible

```yaml
execution_result_python_interpreter: "/path/to/venv/bin/python"
execution_result_auto_install_packages: true
```

### Strict Environments

If you do not want runtime package installation attempts:

```yaml
execution_result_auto_install_packages: false
```

## Troubleshooting

### `pip` not available

Install `pip` in the execution environment image or use a different Python interpreter that already includes it.

### `--user` install fails

The container may be read-only or the Python environment may disable user site-packages. Pre-build the execution environment image instead.

### Import still fails after install

Common causes:

- The role is using a different interpreter than the one that performed the install.
- `pip` installed into a path not visible to the configured interpreter.
- The package installed successfully but the module import failed due to missing native dependencies.

### PostgreSQL in AWX

Use `execution_result_python_interpreter: "python3"` unless you have a custom image with a different interpreter path. Do not point the role to a host-level virtual environment path from inside an execution environment container.
