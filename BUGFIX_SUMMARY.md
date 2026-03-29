# Bug Fix Summary - Collection Module Resolution Error

**Date**: March 30, 2026  
**Issue**: `couldn't resolve module/action 'community.postgresql.postgresql_ping'`

## Problem Description

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

### 3. Updated Documentation ([README.md](README.md))

Enhanced the "Missing Ansible Collections Error" troubleshooting section with:
- Explanation of the issue and when it occurs
- Clear solutions for AWX/Tower and standalone Ansible
- Note that connectivity checks no longer require collections
- Guidance on pre-installing collections in execution environments

## Impact

### What Still Works
✅ Database connectivity checks (now use Python directly)  
✅ Python package verification  
✅ Automatic collection installation attempts  
✅ All other role functionality  

### What Changed
⚠️ Connectivity checks no longer use collection modules (now use Python)  
ℹ️ Better error messages when collections are unavailable  
ℹ️ Clearer guidance on collection installation  

### What Still Requires Collections
❗ Actual database operations (INSERT, SELECT) still require appropriate collections  
❗ For production use, collections should be pre-installed in execution environments  

## Best Practices Going Forward

### For AWX/Tower Users
1. **Pre-install collections in execution environments** (recommended approach)
   - See [AWX Execution Environment Setup](README.md#awx-execution-environment-setup)
   - Build custom EE images with collections included
   - This eliminates runtime collection installation issues

2. **If collections can't be pre-installed**:
   - First playbook run may fail if collections aren't available
   - Second run will succeed (collections installed in first run)
   - Consider this when designing job templates

### For Standalone Ansible Users  
1. Install collections before running playbooks:
   ```bash
   ansible-galaxy collection install community.postgresql community.mysql community.general community.mongodb
   ```

2. Verify installation:
   ```bash
   ansible-galaxy collection list | grep community
   ```

## Testing Recommendations

Test the role in the following scenarios:
- [x] Fresh environment without collections pre-installed
- [x] Environment with collections already installed  
- [ ] AWX/Tower with custom execution environment
- [ ] Standalone Ansible with manual collection installation
- [ ] Second playbook run after first-run collection installation

## Related Files Modified

- `tasks/prerequisites.yml` - Database connectivity checks
- `tasks/main.yml` - Collection installation and error handling
- `README.md` - Troubleshooting documentation

## Migration Notes

No migration required. This is a backward-compatible bug fix that:
- Improves reliability in environments where collections aren't pre-installed
- Maintains all existing functionality
- Provides better error messages and guidance

Users who have already pre-installed collections in their environments will see no behavioral changes.
