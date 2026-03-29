# Diagnostic Improvements for Database Verification

**Date**: March 30, 2026  
**Issue**: Database verification reporting "database does not exist" when it actually exists

## Problem Analysis

From job_127.txt logs:
- Database 'ansible_execution_results' reported as not found
- Screenshot shows the database DOES exist with both tables (failed_jobs, success_jobs)
- psycopg2 warning appears: "psycopg2-binary is required for PostgreSQL"

## Root Cause Investigation

The issue appears to be one of:

1. **psycopg2 not installed**: The warning suggests psycopg2 is missing, which would cause the import to fail
2. **Masked errors**: The old error handling treated all exceptions the same way, making it unclear if the issue was:
   - ImportError (psycopg2 not installed) 
   - Connection error (can't reach database)
   - Query error (database doesn't exist)

## Changes Made

### 1. Separated Import Errors from Connection/Query Errors

**Before**: All errors resulted in generic failure
```python
try:
    import psycopg2
    # ... connection and query code ...
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(2)
```

**After**: Distinct handling for different error types
```python
try:
    import psycopg2
except ImportError as e:
    print(f'ERROR: psycopg2 module not found: {e}')
    print('Please install psycopg2-binary: pip install psycopg2-binary')
    sys.exit(2)  # Exit code 2 = module not installed

try:
    # connection and query code
    if result:
        sys.exit(0)  # Exit code 0 = database exists
    else:
        sys.exit(1)  # Exit code 1 = database not found
except Exception as e:
    print(f'ERROR: Database check failed: {e}')
    sys.exit(2)  # Exit code 2 = connection/query error
```

### 2. Added Debug Output

**Changed**:
- `no_log: true` → `no_log: false` (show actual errors)
- `failed_when: _db_exists_check.rc == 2` → `failed_when: false` (don't fail task, check later)

**Added debug task**:
```yaml
- name: Debug - Show database check result
  ansible.builtin.debug:
    msg:
      - "Database check return code: {{ _db_exists_check.rc }}"
      - "Database check stdout: {{ _db_exists_check.stdout_lines }}"
      - "Database check stderr: {{ _db_exists_check.stderr_lines | default([]) }}"
  when: _db_exists_check.rc != 0
```

### 3. Clearer Error Messages

**Before**: Single generic error message
```yaml
- name: Fail if database does not exist
  ansible.builtin.fail:
    msg: "Database '{{ execution_result_db_name }}' does not exist..."
  when: _db_exists_check.rc != 0
```

**After**: Separate messages for different scenarios
```yaml
- name: Fail if psycopg2 is not available
  ansible.builtin.fail:
    msg:
      - "psycopg2 module is not installed on localhost."
      - "Install it with: pip install psycopg2-binary"
  when: _db_exists_check.rc == 2

- name: Fail if database does not exist
  ansible.builtin.fail:
    msg: "Database '{{ execution_result_db_name }}' does not exist... Output: {{ _db_exists_check.stdout }}"
  when: _db_exists_check.rc == 1
```

## Exit Code Meanings

| Exit Code | Meaning | Action Required |
|-----------|---------|-----------------|
| 0 | Database/table exists | Continue normally |
| 1 | Database/table NOT FOUND | Create the database/table |
| 2 | psycopg2 not installed OR connection error | Install psycopg2-binary OR fix connection |

## Next Steps for Testing

Run the playbook again. The improved diagnostics will show:

### If psycopg2 is not installed:
```
TASK [update-db : Debug - Show database check result]
ok: [Ubuntu -> localhost] => {
    "msg": [
        "Database check return code: 2",
        "Database check stdout: ['ERROR: psycopg2 module not found: No module named psycopg2']"
    ]
}

TASK [update-db : Fail if psycopg2 is not available]
fatal: [Ubuntu -> localhost]: FAILED! => {
    "msg": [
        "psycopg2 module is not installed on localhost.",
        "Install it with: pip install psycopg2-binary"
    ]
}
```

### If psycopg2 IS installed but database truly doesn't exist:
```
TASK [update-db : Debug - Show database check result]
ok: [Ubuntu -> localhost] => {
    "msg": [
        "Database check return code: 1",
        "Database check stdout: ['NOT_FOUND']"
    ]
}

TASK [update-db : Fail if database does not exist]
fatal: [Ubuntu -> localhost]: FAILED! => {
    "msg": "Database 'ansible_execution_results' does not exist on 10.0.0.14..."
}
```

### If psycopg2 IS installed AND database exists:
```
TASK [update-db : Verify database exists using Python]
ok: [Ubuntu -> localhost]

# No debug output (rc = 0)
# Continues to table verification
```

## Files Modified

- `tasks/database_postgresql.yml` - All three verification tasks (database, success_jobs table, failed_jobs table)

## Expected Resolution

Based on the warning message, **psycopg2 is likely not installed**. The next run should clearly show:
- Exit code 2
- Error message about psycopg2 module not found
- Clear instructions to install it

**Solution**: Install psycopg2-binary in the AWX execution environment:
```bash
pip install psycopg2-binary
```

Or in the Dockerfile:
```dockerfile
RUN pip3 install --no-cache-dir psycopg2-binary>=2.9.0
```
