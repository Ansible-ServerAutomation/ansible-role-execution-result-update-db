# Workspace Instructions: ansible-role-execution-result-update-db

> Ansible role for storing execution results from ansible-role-execution-result into databases (PostgreSQL, MySQL, SQLite, MongoDB)

## Quick Start

**Test the role locally:**
```bash
# 1. Setup Python environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install database drivers
pip install psycopg2-binary PyMySQL pymongo

# 3. Create test database (PostgreSQL example)
python scripts/setup_postgresql_database.py --host 10.0.0.14 --user postgres --password <pwd>

# 4. Test connectivity
python scripts/test_postgresql_connectivity.py --host 10.0.0.14 --user postgres --password <pwd>

# 5. Run example playbook
ansible-playbook examples/example_playbook.yml --ask-vault-pass
```

**Install required Ansible collections:**
```bash
ansible-galaxy collection install community.postgresql community.mysql community.mongodb community.general
```

## Project Architecture

### Core Principles

1. **Localhost Delegation**: ALL database operations run on `localhost` via `delegate_to: localhost` at block level
   - Database connections happen from control node, not managed hosts
   - Ensures consistent database access regardless of inventory targets

2. **Ansible Collection Modules**: All database types (PostgreSQL, MySQL, MongoDB) use their respective Ansible collection modules
   - PostgreSQL: Uses `community.postgresql` collection modules (`postgresql_query`)
   - MySQL: Uses `community.mysql` collection modules
   - MongoDB: Uses `community.mongodb` collection modules
   - Requires pre-installation of collections in AWX/Tower execution environments

3. **No Schema Management**: This role does NOT create databases or tables
   - Verifies existence and fails fast if infrastructure isn't ready
   - Use `scripts/setup_postgresql_database.py` for database setup
   - See [docs/DATABASE_SETUP.md](../docs/DATABASE_SETUP.md) for DDL scripts

4. **Dual-Table Pattern**: Records route based on return code
   - `return_code == 0` → `success_jobs` table  
   - `return_code != 0` → `failed_jobs` table

### Directory Structure

```
tasks/
├── main.yml                    # Orchestration: prerequisite → capture → prepare → database
├── prerequisites.yml           # Python package checks, connectivity tests
├── capture_artifacts.yml       # Read execution_results fact from ansible-role-execution-result
├── prepare_data.yml            # Validate, truncate fields, split success/failed records
├── database_postgresql.yml     # PostgreSQL operations (uses community.postgresql)
├── database_mysql.yml          # MySQL operations (uses community.mysql collection)
├── database_sqlite.yml         # SQLite operations (uses community.general collection)
└── database_mongodb.yml        # MongoDB operations (uses community.mongodb collection)

scripts/
├── setup_postgresql_database.py       # Automated database/table creation
└── test_postgresql_connectivity.py    # Connection verification tool

docs/
└── DATABASE_SETUP.md           # DDL scripts for all database types
```

### Variable Conventions

- **Public variables**: `execution_result_*` (in [defaults/main.yml](../defaults/main.yml))
- **Internal state**: `_execution_result_*` (underscore prefix = private)
- **Immutable maps**: [vars/main.yml](../vars/main.yml) (collection requirements, defaults)

**Key variables:**
- `execution_result_python_interpreter`: Path to Python with database drivers (`"python3"` for AWX, `"/path/to/venv/bin/python"` for standalone)
- `execution_result_db_type`: `"postgresql"`, `"mysql"`, `"sqlite"`, or `"mongodb"`
- `execution_result_fail_on_db_error`: `true` = fail on errors, `false` = warn and continue

## Common Development Tasks

### Making Changes to Database Logic

1. **PostgreSQL changes** → Edit [tasks/database_postgresql.yml](../tasks/database_postgresql.yml)
   - Uses `community.postgresql.postgresql_query` module for all database operations
   - Requires `community.postgresql` collection to be installed
   - Simpler and more maintainable than direct Python approach

2. **MySQL/MongoDB changes** → Edit respective task files
   - These use Ansible collection modules (community.mysql, community.mongodb)
   - Collection modules require pre-installation in execution environments

3. **Data preparation/validation** → Edit [tasks/prepare_data.yml](../tasks/prepare_data.yml)
   - Field truncation: `field[:execution_result_max_field_length]`
   - Record splitting: `when: item.status == 'SUCCESS'` vs others

### Testing Changes

**No automated test framework exists.** Use manual testing:

1. Create test database: `python scripts/setup_postgresql_database.py --host <host> --user <user> --password <pwd>`
2. Modify role tasks
3. Run example playbook: `ansible-playbook examples/example_playbook.yml`
4. Verify records in database: `psql -h <host> -U <user> -d ansible_execution_results -c "SELECT * FROM failed_jobs;"`

### Adding New Database Type

1. Create `tasks/database_<type>.yml` following existing patterns
2. Add collection requirement to [vars/main.yml](../vars/main.yml) `_execution_result_collection_map`
3. Add Python package check to [tasks/prerequisites.yml](../tasks/prerequisites.yml)
4. Update [docs/DATABASE_SETUP.md](../docs/DATABASE_SETUP.md) with DDL
5. Add example to [examples/example_playbook.yml](../examples/example_playbook.yml)

## Critical Patterns & Anti-Patterns

### ✅ DO

- **Use `delegate_to: localhost`** at block level for all database operations
- **Use `run_once: true`** for database verification tasks (avoid redundant checks)
- **Use Ansible collection modules** for all database operations (PostgreSQL, MySQL, MongoDB)
- **Use `no_log: false` on diagnostic tasks** for visibility during troubleshooting
- **Truncate long fields** using slice notation: `[:max_length]`
- **Test with AWX/Tower** to catch execution environment issues early
- **Pre-install collections** in execution environments for AWX/Tower deployments

### ❌ DON'T

- **Never use collection modules without pre-installing collections**
  - Collections must be pre-installed in AWX/Tower execution environments
  - Collections installed during playbook execution aren't available for module resolution
  - Parse-time errors can't be caught by rescue blocks
  - Solution: Pre-install collections in execution environment definition

- **Never place module names as block-level attributes**
  ```yaml
  # ❌ WRONG - will cause "not a valid attribute for a Block" error
  - name: Task
    ansible.builtin.set_fact:
      var: value
  delegate_to: localhost
  ansible.builtin.set_fact:  # ← INVALID here
    var: value
  
  # ✅ CORRECT
  - name: Task
    ansible.builtin.set_fact:
      var: value
  delegate_to: localhost
  ```

- **Never assume Python interpreter path exists**
  - Always validate with exit code 127 check
  - Exit code 127 = "command not found" (interpreter doesn't exist)
  - Add helpful error message with common solutions

- **Never mix AWX localhost with actual host localhost**
  - In AWX, `localhost` = execution environment container (`/runner/`)
  - For venvs on actual Tower host, use explicit inventory entry with connection delegation

## Known Issues & Solutions

See [BUGFIX_SUMMrequirements**: All database types now use Ansible collection modules → Pre-install in execution environments
2. **Invalid Python interpreter path (exit code 127)**: Path doesn't exist → Validate and provide helpful error
3. **Invalid Python interpreter path (exit code 127)**: Path doesn't exist → Validate and provide helpful error
3. **Masked import errors**: ImportError vs ConnectionError indistinguishable → Separate error handling with distinct exit codes
4. **YAML block attribute errors**: Module names at block level → Only use valid block directives (delegate_to, when, rescue, etc.)

## Documentation

- **[README.md](../README.md)**: Feature overview, installation, configuration
- **[docs/DATABASE_SETUP.md](../docs/DATABASE_SETUP.md)**: DDL scripts for all database types  
- **[BUGFIX_SUMMARY.md](../BUGFIX_SUMMARY.md)**: Detailed bug fix history with solutions
- **[DIAGNOSTIC_IMPROVEMENTS.md](../DIAGNOSTIC_IMPROVEMENTS.md)**: Error handling improvements

## AWX/Tower-Specific Guidance

### Execution Environment Setup
All database types require pre-installed collections in execution environments:**

```dockerfile
# In your EE definition
RUN pip3 install --no-cache-dir psycopg2-binary>=2.9.0 PyMySQL>=1.0.0 pymongo>=4.0.0
```

```yaml
# execution-environment.yml
dependencies:
  galaxy: requirements.yml
  python: requirements.txt

# requirements.yml
collections:
  - name: community.postgresql
    version: ">=3.0.0"ts.yml
collections:
  - name: community.mysql
    version: ">=3.0.0"
  - name: community.mongodb
    version: ">=1.0.0"
```

### Python Interpreter Configuration

- **AWX Execution Environment**: Use `execution_result_python_interpreter: "python3"` (container Python)
- **Standalone Ansible**: Use `execution_result_python_interpreter: "/path/to/venv/bin/python"` (venv path)
- **Hybrid (venv on Tower host)**: Create inventory entry for actual Tower host, not `localhost`

### Common AWX Errors

**"Python interpreter not found" (exit code 127)**:
- `localhost` in AWX = container, not actual Tower VM
- Virtual environments on Tower host aren't accessible in container
- Solution: Use container Python or create proper inventory delegation

**All database types require collections pre-installed (community.postgresql, community.mysql, community.mongodb)
- MySQL/MongoDB still require collections pre-installed
- Can't install collections at runtime in AWX
- Solution: Build custom EE with collections included

## Related Roles

- **[ansible-role-execution-result](https://github.com/Ansible-ServerAutomation/ansible-role-execution-result)**: Captures execution metadata (this role's data source)
  - Sets `execution_results` fact consumed by this role
  - Call execution-result role BEFORE this role in playbooks

## Getting Help

When reporting issues, include:
1. Database type and version
2. AWX/Tower vs standalone Ansible
3. Python interpreter path configured
4. Relevant task output (run with `-vvv` for verbose)
5. Database connectivity test results: `python scripts/test_postgresql_connectivity.py ...`
