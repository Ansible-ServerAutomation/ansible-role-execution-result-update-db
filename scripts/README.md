# PostgreSQL Scripts for ansible-role-execution-result-update-db

This folder contains scripts for PostgreSQL database connectivity testing and setup.

## Prerequisites

### For Python Script
Install the required PostgreSQL adapter:
```bash
pip install psycopg2-binary
```

## Usage

### Python Script (Recommended)

**Basic test with default database:**
```bash
python test_postgresql_connectivity.py --host 10.0.0.14 --port 5432 --username postgres --password yourpassword
```

**Test with specific database:**
```bash
python test_postgresql_connectivity.py --host 10.0.0.14 --port 5432 --username dbuser --password secret --database mydb
```

**Short form arguments:**
```bash
python test_postgresql_connectivity.py -H 10.0.0.14 -p 5432 -u postgres -P yourpassword -d testdb
```

### Parameters

| Parameter | Short | Required | Default | Description |
|-----------|-------|----------|---------|-------------|
| --host | -H | Yes | - | PostgreSQL server IP address or hostname |
| --port | -p | No | 5432 | PostgreSQL server port number |
| --username | -u | Yes | - | Database username |
| --password | -P | Yes | - | Database password |
| --database | -d | No | postgres | Database name to connect to |

## Example Output

### Successful Connection
```
============================================================
PostgreSQL Connectivity Test
============================================================
Host:     10.0.0.14
Port:     5432
Username: postgres
Database: postgres
============================================================

Attempting to connect to PostgreSQL server...
✓ Connection successful!

PostgreSQL Version:
PostgreSQL 14.5 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 11.2.0, 64-bit

Connected to database: postgres
Connected as user: postgres

============================================================
Status: SUCCESS - All connectivity tests passed!
============================================================
```

### Failed Connection
```
============================================================
PostgreSQL Connectivity Test
============================================================
Host:     10.0.0.14
Port:     5432
Username: postgres
Database: postgres
============================================================

Attempting to connect to PostgreSQL server...
✗ Connection failed!

Operational Error: could not connect to server: Connection refused

Possible causes:
  - PostgreSQL server is not running
  - Incorrect host/port configuration
  - Network connectivity issues
  - Firewall blocking the connection

============================================================
Status: FAILED
============================================================
```

## Testing Your PostgreSQL Server (10.0.0.14)

For your specific PostgreSQL server at `10.0.0.14`, use:

```bash
python test_postgresql_connectivity.py --host 10.0.0.14 --port 5432 --username YOUR_USERNAME --password YOUR_PASSWORD
```

Replace `YOUR_USERNAME` and `YOUR_PASSWORD` with your actual credentials.

---

## Database Setup Script

### setup_postgresql_database.py

This script initializes the PostgreSQL database and creates the required tables for storing Ansible execution results. It creates:

1. **Database**: `ansible_execution_results` (configurable)
2. **Tables**: 
   - `success_jobs` - Stores successful execution results
   - `failed_jobs` - Stores failed execution results
3. **Indexes**: Optimized indexes on timestamp, project, playbook, and failed_task fields

### Usage

**Basic setup with defaults:**
```bash
python setup_postgresql_database.py --host localhost --username postgres --password mypass
```

**Setup with custom database and table names:**
```bash
python setup_postgresql_database.py --host 10.0.0.14 --username dbadmin --password secret \
  --database my_ansible_db --table-success my_success --table-failed my_failed
```

**Dry-run to preview SQL statements (recommended first run):**
```bash
python setup_postgresql_database.py --host localhost --username postgres --password mypass --dry-run
```

**Drop and recreate tables (WARNING: destroys existing data):**
```bash
python setup_postgresql_database.py --host localhost --username postgres --password mypass --drop-tables
```

**Setup with SSL connection:**
```bash
python setup_postgresql_database.py --host db.example.com --username postgres --password mypass \
  --ssl-mode require
```

### Parameters

| Parameter | Short | Required | Default | Description |
|-----------|-------|----------|---------|-------------|
| --host | -H | Yes | - | PostgreSQL server IP address or hostname |
| --port | -p | No | 5432 | PostgreSQL server port number |
| --username | -u | Yes | - | Database username (must have CREATE DATABASE privileges) |
| --password | -P | Yes | - | Database password |
| --database | -d | No | ansible_execution_results | Database name to create |
| --table-success | - | No | success_jobs | Table name for successful executions |
| --table-failed | - | No | failed_jobs | Table name for failed executions |
| --ssl-mode | - | No | prefer | SSL mode (disable, allow, prefer, require, verify-ca, verify-full) |
| --dry-run | - | No | False | Preview SQL statements without executing |
| --drop-tables | - | No | False | Drop existing tables before creating (destroys data!) |
| --skip-verification | - | No | False | Skip verification step after creation |

### Database Schema

Both tables (`success_jobs` and `failed_jobs`) contain 29 columns:

**Core Fields:**
- `id` - Auto-incrementing primary key
- `timestamp` - Execution timestamp
- `status` - Execution status (SUCCESS/FAILURE/UNKNOWN)

**Host Information:**
- `hostname` - System hostname
- `inventory_hostname` - Ansible inventory hostname
- `ansible_host` - Ansible host variable

**Job Metadata:**
- `project` - AWX/Tower project name
- `organization` - AWX/Tower organization
- `job_template` - AWX/Tower job template
- `playbook` - Playbook filename
- `scm_url` - Git repository URL
- `scm_branch` - Git branch
- `scm_revision` - Git commit SHA
- `execution_environment` - Execution environment name

**Execution Details:**
- `return_code` - Task return code
- `message` - Task message/error
- `stdout` - Standard output
- `stderr` - Standard error
- `exception` - Exception traceback
- `warnings` - Task warnings (JSONB)
- `failed_task` - Name of failed task
- `failed_task_module` - Module that failed

**System Information:**
- `os_distribution` - OS distribution (e.g., Ubuntu)
- `os_version` - OS version
- `os_family` - OS family (e.g., Debian)
- `os_system` - System type (e.g., Linux)
- `os_architecture` - Architecture (e.g., x86_64)

**Metadata:**
- `created_at` - Record creation timestamp
- `updated_at` - Record update timestamp

### Indexes

**success_jobs table:**
- `idx_success_jobs_timestamp` - On timestamp column
- `idx_success_jobs_project` - On project column
- `idx_success_jobs_playbook` - On playbook column

**failed_jobs table:**
- `idx_failed_jobs_timestamp` - On timestamp column
- `idx_failed_jobs_project` - On project column
- `idx_failed_jobs_failed_task` - On failed_task column

### Example Output

#### Successful Setup
```
======================================================================
PostgreSQL Database Setup for ansible-role-execution-result-update-db
======================================================================
Host:                 localhost
Port:                 5432
Username:             postgres
Database:             ansible_execution_results
Success Table:        success_jobs
Failed Table:         failed_jobs
SSL Mode:             prefer (default)
Mode:                 EXECUTE
======================================================================

======================================================================
STEP 1: Database Creation
======================================================================
✓ Database 'ansible_execution_results' already exists (skipped)

======================================================================
STEP 2: Table and Index Creation
======================================================================

Creating table 'success_jobs'...
✓ Table 'success_jobs' created
Creating indexes for 'success_jobs'...
✓ Indexes created for 'success_jobs'

Creating table 'failed_jobs'...
✓ Table 'failed_jobs' created
Creating indexes for 'failed_jobs'...
✓ Indexes created for 'failed_jobs'

======================================================================
Table Summary
======================================================================
  failed_jobs: 29 columns
  success_jobs: 29 columns

======================================================================
STEP 3: Verification
======================================================================

Tables found: 2
  ✓ failed_jobs
  ✓ success_jobs

Indexes found: 8
  ✓ failed_jobs.failed_jobs_pkey
  ✓ failed_jobs.idx_failed_jobs_failed_task
  ✓ failed_jobs.idx_failed_jobs_project
  ✓ failed_jobs.idx_failed_jobs_timestamp
  ✓ success_jobs.idx_success_jobs_playbook
  ✓ success_jobs.idx_success_jobs_project
  ✓ success_jobs.idx_success_jobs_timestamp
  ✓ success_jobs.success_jobs_pkey

✓ Verification PASSED - All required tables exist

======================================================================
Status: SUCCESS - Database setup completed successfully!
======================================================================

Database 'ansible_execution_results' is ready to receive Ansible execution results.
Tables created: success_jobs, failed_jobs

You can now configure your Ansible role with:
  execution_result_db_host: localhost
  execution_result_db_port: 5432
  execution_result_db_name: ansible_execution_results
  execution_result_db_table_success: success_jobs
  execution_result_db_table_failed: failed_jobs
```

#### Dry-Run Output
```
======================================================================
STEP 1: Database Creation
======================================================================
[DRY RUN] Would create database: ansible_execution_results
[DRY RUN] SQL: CREATE DATABASE ansible_execution_results;

======================================================================
STEP 2: Table and Index Creation
======================================================================

[DRY RUN] Would execute on database 'ansible_execution_results':

-- Create success_jobs table
CREATE TABLE IF NOT EXISTS success_jobs (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL,
  hostname VARCHAR(255),
  ...
);

-- Create indexes for success_jobs
CREATE INDEX IF NOT EXISTS idx_success_jobs_timestamp ON success_jobs(timestamp);
CREATE INDEX IF NOT EXISTS idx_success_jobs_project ON success_jobs(project);
CREATE INDEX IF NOT EXISTS idx_success_jobs_playbook ON success_jobs(playbook);

-- Create failed_jobs table
CREATE TABLE IF NOT EXISTS failed_jobs (
  ...
);

-- Create indexes for failed_jobs
CREATE INDEX IF NOT EXISTS idx_failed_jobs_timestamp ON failed_jobs(timestamp);
CREATE INDEX IF NOT EXISTS idx_failed_jobs_project ON failed_jobs(project);
CREATE INDEX IF NOT EXISTS idx_failed_jobs_failed_task ON failed_jobs(failed_task);

======================================================================
Status: DRY RUN COMPLETE - No changes made
======================================================================
```

### Workflow Recommendation

1. **Test connectivity first:**
   ```bash
   python test_postgresql_connectivity.py --host localhost --username postgres --password mypass
   ```

2. **Preview changes with dry-run:**
   ```bash
   python setup_postgresql_database.py --host localhost --username postgres --password mypass --dry-run
   ```

3. **Execute setup:**
   ```bash
   python setup_postgresql_database.py --host localhost --username postgres --password mypass
   ```

4. **Configure Ansible role** with the database connection details in your playbook variables or `defaults/main.yml`

### Notes

- The script is **idempotent** - you can run it multiple times safely. It uses `IF NOT EXISTS` clauses.
- The user must have **CREATE DATABASE** privileges to create the database.
- Use `--drop-tables` with caution as it will **permanently delete all data** in the tables.
- Tables are created in the `public` schema by default.
- The script automatically creates indexes for optimal query performance.

---

## Troubleshooting

### psycopg2 installation issues
If you encounter issues installing `psycopg2`, try:
```bash
# On Linux/Mac
pip install psycopg2-binary

# On Windows
pip install psycopg2-binary

# If using Anaconda
conda install -c anaconda psycopg2
```

### Connection Issues
1. **Verify PostgreSQL is running** on the server
2. **Check firewall settings** - Port 5432 should be accessible
3. **Verify pg_hba.conf** - Ensure your IP is allowed to connect
4. **Check postgresql.conf** - Ensure `listen_addresses` is properly configured
5. **Test network connectivity** - Use `ping` or `telnet` to verify network access

### Network Test
```bash
# Test if port is accessible
telnet 10.0.0.14 5432

# Or using PowerShell on Windows
Test-NetConnection -ComputerName 10.0.0.14 -Port 5432
```
