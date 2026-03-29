# Bug Fix Summary - Collection Module Resolution & YAML Syntax Errors

**Date**: March 30, 2026  
**Issues Fixed**:
1. `couldn't resolve module/action 'community.postgresql.postgresql_ping'` (prerequisites.yml)
2. `'ansible.builtin.set_fact' is not a valid attribute for a Block` (database_postgresql.yml)
3. `couldn't resolve module/action 'community.postgresql.postgresql_query'` (database_postgresql.yml)

## Problem 1: Collection Module Resolution Error

When the role was executed in AWX/Tower environments where Ansible collections were not pre-installed, the following error occurred:

```
ERROR! couldn't resolve module/action 'community.postgresql.postgresql_ping'. 
This often indicates a misspelling, missing collection, or incorrect module path.

The error appears to be in '/runner/requirements_roles/update-db/tasks/prerequisites.yml': line 50
```

### Root Cause

The role attempted to:
1. Install the required Ansible collection (`community.postgresql`) at runtime using `ansible-galaxy collection install`
2. Immediately use collection modules (e.g., `community.postgresql.postgresql_ping`) in subsequent tasks

However, **Ansible collections installed during playbook execution are not immediately available** in the current execution context. The collection modules couldn't be resolved because Ansible parses all task files at the beginning of the play, before the collection was installed.

This created a **parse-time error** that couldn't be caught by rescue blocks (which only catch runtime errors).

## Problem 2: YAML Syntax Error in database_postgresql.yml

```
ERROR! 'ansible.builtin.set_fact' is not a valid attribute for a Block

The error appears to be in '/runner/requirements_roles/update-db/tasks/database_postgresql.yml': line 4, column 3
```

### Root Cause

The `database_postgresql.yml` file had malformed YAML at the end of the main block:

```yaml
    - name: Set records processed count
      ansible.builtin.set_fact:
        _execution_result_records_processed: "{{ ... }}"
  delegate_to: localhost
  ansible.builtin.set_fact:    # ← INVALID: Can't have module name as block attribute
    _execution_result_records_processed: "{{ ... }}"
```

Lines 205-206 contained a duplicate `ansible.builtin.set_fact:` at the block level, which is not a valid YAML structure. Block-level attributes can include `when`, `delegate_to`, `rescue`, etc., but not module names like `ansible.builtin.set_fact`.

This was likely a copy-paste error that duplicated the set_fact task content at the block level.

## Problem 3: Collection Module Resolution Error in Database Operations

After fixing Problems 1 and 2, a third error appeared in job 125:

```
ERROR! couldn't resolve module/action 'community.postgresql.postgresql_query'. 
This often indicates a misspelling, missing collection, or incorrect module path.

The error appears to be in '/runner/requirements_roles/update-db/tasks/database_postgresql.yml': line 22, column 7
```

### Root Cause

Even though we fixed the connectivity checks in `prerequisites.yml` to use Python directly, the actual database operations in `database_postgresql.yml` still used collection modules:
- `community.postgresql.postgresql_query` for database/table verification
- `community.postgresql.postgresql_query` for INSERT operations

These modules caused the same parse-time error because the collection wasn't available in the execution context.

### Solution

Convert **all** PostgreSQL operations to use Python/psycopg2 directly instead of Ansible collection modules. This makes the role completely independent of Ansible collections for PostgreSQL:
- Database existence checks → Python with psycopg2
- Table existence checks → Python with psycopg2
- INSERT operations → Python with psycopg2

## Changes Made

### 1. Updated Database Connectivity Checks ([tasks/prerequisites.yml](tasks/prerequisites.yml))

**Before**: Used collection-specific modules
```yaml
- name: Test PostgreSQL connection
  community.postgresql.postgresql_ping:
    login_host: "{{ execution_result_db_host }}"
    # ... other parameters
```

**After**: Uses Python directly via command module
```yaml
- name: Test PostgreSQL connection using Python
  ansible.builtin.command:
    cmd: >
      python3 -c "import psycopg2; conn = psycopg2.connect(
      host='{{ execution_result_db_host }}',
      port={{ execution_result_db_port }},
      user='{{ execution_result_db_user }}',
      password='{{ execution_result_db_password }}',
      database='{{ execution_result_db_name }}',
      connect_timeout=10); conn.close(); print('SUCCESS')"
  register: _db_ping_result
  changed_when: false
  failed_when: false
  no_log: true
```

**Benefits**:
- No dependency on collection modules for connectivity checks
- Works immediately after Python package installation
- More reliable in dynamic environments
- Consistent behavior across different Ansible versions

### 2. Enhanced Error Handling ([tasks/main.yml](tasks/main.yml))

Added informative notices and comprehensive error handling:

```yaml
- name: Display collection installation notice
  ansible.builtin.debug:
    msg:
      - "NOTICE: Collection {{ _execution_result_collection_map[execution_result_db_type] }} was just installed."
      - "If you encounter module resolution errors, the collection may not be available in the current execution context."
      - "For best results, pre-install collections in your execution environment."

- name: Include database-specific tasks
  block:
    - name: Execute database operations
      ansible.builtin.include_tasks: "database_{{ execution_result_db_type }}.yml"
  rescue:
    - name: Handle database operation failure
      ansible.builtin.fail:
        msg:
          - "Failed to execute database operations..."
          - "Required collection: {{ _execution_result_collection_map[execution_result_db_type] }}"
          - "Solution: Pre-install the collection in your execution environment or run the playbook again."
```

### 3. Fixed YAML Syntax Error ([tasks/database_postgresql.yml](tasks/database_postgresql.yml))

**Before** (lines 200-207):
```yaml
    - name: Set records processed count
      ansible.builtin.set_fact:
        _execution_result_records_processed: "{{ (_execution_results_success | length) + (_execution_results_failed | length) }}"
  delegate_to: localhost
  ansible.builtin.set_fact:    # ← INVALID at block level
    _execution_result_records_processed: "{{ (_execution_results_success | length) + (_execution_results_failed | length) }}"

- name: Debug - Show insert results
```

**After** (lines 200-206):
```yaml
    - name: Set records processed count
      ansible.builtin.set_fact:
        _execution_result_records_processed: "{{ (_execution_results_success | length) + (_execution_results_failed | length) }}"
  delegate_to: localhost

- name: Debug - Show insert results
```

**Benefits**:
- Correct YAML syntax structure
- Block properly closes with only valid block-level attributes
- No duplicate task definitions

### 4. Converted All PostgreSQL Operations to Python ([tasks/database_postgresql.yml](tasks/database_postgresql.yml))

**Completely eliminated dependency on `community.postgresql` collection** by converting all database operations to use Python/psycopg2 directly.

**Changed Operations**:

1. **Database existence verification** - Now uses Python heredoc style:
```yaml
- name: Verify database exists using Python
  ansible.builtin.shell: |
    python3 << 'EOF'
    import psycopg2
    import sys
    try:
        conn = psycopg2.connect(...)
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', ('{{ execution_result_db_name }}',))
        result = cur.fetchone()
        # ... check result and exit accordingly
    EOF
```

2. **Table existence verification** - Same Python approach for both success_jobs and failed_jobs tables

3. **INSERT operations** - Completely rewritten to use Python with JSON data:
```yaml
- name: Insert success records via psycopg2
  ansible.builtin.shell:
    cmd: |
      python3 << 'EOFPYTHON'
      import psycopg2
      import json
      import sys
      
      record = json.loads('''{{ item | to_json }}''')
      
      try:
          conn = psycopg2.connect(...)
          cur = conn.cursor()
          cur.execute("""INSERT INTO {{ execution_result_db_table_success }} (...) VALUES (...)""", record)
          conn.commit()
          # ...
      EOFPYTHON
  loop: "{{ _execution_results_success }}"
```

**Benefits**:
- ✅ **No Ansible collection required** for PostgreSQL operations
- ✅ **No parse-time errors** - all operations use built-in `ansible.builtin.shell`
- ✅ **Works immediately** after psycopg2 installation
- ✅ **Consistent approach** across all database operations
- ✅ **Better error handling** with Python exceptions
- ✅ **Simplified dependencies** - only needs Python + psycopg2

**YAML Formatting**: Used heredoc style (`<< 'EOF'`) to avoid quote escaping issues in YAML when embedding Python code.

### 5. Updated Documentation ([README.md](README.md))

Enhanced the "Missing Ansible Collections Error" troubleshooting section with:
- Explanation of the issue and when it occurs
- Clear solutions for AWX/Tower and standalone Ansible
- Note that connectivity checks no longer require collections
- Guidance on pre-installing collections in execution environments

## Impact

### What Still Works
✅ All database connectivity checks (use Python directly)  
✅ All PostgreSQL database operations (use Python/psycopg2 directly)  
✅ Python package verification  
✅ Automatic collection installation (for other database types)  
✅ All other role functionality  

### What Changed (PostgreSQL Only)
🔄 **No longer requires `community.postgresql` collection** - all operations use Python  
🔄 Connectivity checks use Python directly (bash heredoc style)  
🔄 Database/table verification uses Python directly  
🔄 INSERT operations use Python/psycopg2 directly  
ℹ️ Better error messages and diagnostics  
ℹ️ Clearer guidance on dependencies  

### What Still Requires Collections
❗ **MySQL** operations still require `community.mysql` collection  
❗ **MongoDB** operations still require `community.mongodb` collection  
❗ **SQLite** operations (minimal collection usage)  
✅ **PostgreSQL** operations **NO LONGER require** `community.postgresql` collection

### Current Dependencies by Database Type

| Database | Python Package | Ansible Collection | Notes |
|----------|---------------|-------------------|-------|
| PostgreSQL | `psycopg2-binary` | ✅ **NOT REQUIRED** | All operations use Python directly |
| MySQL | `PyMySQL` | ❗ Required | Still uses collection modules |
| MongoDB | `pymongo` | ❗ Required | Still uses collection modules |
| SQLite | (built-in) | (minimal) | Built-in support |

## Best Practices Going Forward

### For PostgreSQL Users (UPDATED)
**You NO LONGER need to pre-install `community.postgresql` collection!**

Simply ensure `psycopg2-binary` is installed in your execution environment:
```bash
pip install psycopg2-binary
```

The role will work immediately without any Ansible collection dependencies for PostgreSQL.

### For AWX/Tower Users (PostgreSQL)
1. **Install psycopg2 in your execution environment**:
   ```dockerfile
   RUN pip3 install --no-cache-dir psycopg2-binary>=2.9.0
   ```

2. **No need to install `community.postgresql` collection** for this role

### For MySQL/MongoDB Users
1. **Still need to pre-install collections** in execution environments
   - See [AWX Execution Environment Setup](README.md#awx-execution-environment-setup)  
   - Build custom EE images with collections included

2. **Or accept first-run failures**:
   - First playbook run may fail if collections aren't available
   - Second run will succeed (collections installed in first run)
   - Consider this when designing job templates

### For Standalone Ansible Users (PostgreSQL)
**No collection installation needed** for PostgreSQL operations. Just install psycopg2:
```bash
pip install psycopg2-binary
```

### For Standalone Ansible Users (Other Databases)
Install required collections before running playbooks:
```bash
ansible-galaxy collection install community.mysql community.general community.mongodb
```

## Testing Recommendations

Test the role in the following scenarios:
- [x] Fresh environment without collections pre-installed ✅ (PostgreSQL now works)
- [x] Environment with collections already installed  
- [x] PostgreSQL operations without any Ansible collections ✅ (Problem 3 fix)
- [ ] AWX/Tower with custom execution environment
- [ ] Standalone Ansible with manual collection installation  
- [ ] MySQL/MongoDB with runtime collection installation

## Related Files Modified

### Problem 1: Collection Module Resolution in Prerequisites
- `tasks/prerequisites.yml` - Converted connectivity checks to Python

### Problem 2: YAML Syntax Error  
- `tasks/database_postgresql.yml` - Fixed duplicate `set_fact` at block level

### Problem 3: Collection Module Resolution in Database Operations
- `tasks/database_postgresql.yml` - Converted ALL PostgreSQL operations to Python:
  - Database existence checks → Python/psycopg2
  - Table existence checks → Python/psycopg2
  - INSERT operations → Python/psycopg2

### Documentation & Error Handling
- `tasks/main.yml` - Enhanced error handling and collection installation notices
- `README.md` - Updated troubleshooting documentation
- `BUGFIX_SUMMARY.md` - This comprehensive change log

## Migration Notes

No migration required. This is a backward-compatible bug fix that:
- Improves reliability in environments where collections aren't pre-installed
- Maintains all existing functionality
- Provides better error messages and guidance

Users who have already pre-installed collections in their environments will see no behavioral changes.
