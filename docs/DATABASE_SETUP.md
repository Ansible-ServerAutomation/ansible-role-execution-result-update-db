# Database Setup Guide

**IMPORTANT**: This role requires that the database and tables already exist. The role will **NOT** create them for you. This is intentional to align with production best practices where applications should not auto-provision infrastructure.

Before using this role, you must create:
1. The database (default: `ansible_execution_results`)
2. The `success_jobs` table
3. The `failed_jobs` table

Use the DDL scripts below for your database type, or use the provided setup script in the `scripts/` directory for PostgreSQL.

## PostgreSQL Setup

```sql
-- Create database
CREATE DATABASE ansible_execution_results;

-- Connect to the database
\c ansible_execution_results

-- Create success_jobs table
CREATE TABLE IF NOT EXISTS success_jobs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    hostname VARCHAR(255),
    inventory_hostname VARCHAR(255),
    ansible_host VARCHAR(255),
    project VARCHAR(255),
    organization VARCHAR(255),
    job_template VARCHAR(255),
    playbook VARCHAR(255),
    scm_url TEXT,
    scm_branch VARCHAR(255),
    scm_revision VARCHAR(255),
    execution_environment VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    return_code INTEGER,
    message TEXT,
    stdout TEXT,
    stderr TEXT,
    exception TEXT,
    warnings TEXT,
    failed_task VARCHAR(500),
    failed_task_module VARCHAR(255),
    os_distribution VARCHAR(100),
    os_version VARCHAR(100),
    os_family VARCHAR(100),
    os_system VARCHAR(100),
    os_architecture VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create failed_jobs table
CREATE TABLE IF NOT EXISTS failed_jobs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    hostname VARCHAR(255),
    inventory_hostname VARCHAR(255),
    ansible_host VARCHAR(255),
    project VARCHAR(255),
    organization VARCHAR(255),
    job_template VARCHAR(255),
    playbook VARCHAR(255),
    scm_url TEXT,
    scm_branch VARCHAR(255),
    scm_revision VARCHAR(255),
    execution_environment VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    return_code INTEGER,
    message TEXT,
    stdout TEXT,
    stderr TEXT,
    exception TEXT,
    warnings TEXT,
    failed_task VARCHAR(500),
    failed_task_module VARCHAR(255),
    os_distribution VARCHAR(100),
    os_version VARCHAR(100),
    os_family VARCHAR(100),
    os_system VARCHAR(100),
    os_architecture VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for success_jobs
CREATE INDEX IF NOT EXISTS idx_success_jobs_timestamp ON success_jobs(timestamp);
CREATE INDEX IF NOT EXISTS idx_success_jobs_project ON success_jobs(project);
CREATE INDEX IF NOT EXISTS idx_success_jobs_playbook ON success_jobs(playbook);
CREATE INDEX IF NOT EXISTS idx_success_jobs_organization ON success_jobs(organization);

-- Create indexes for failed_jobs
CREATE INDEX IF NOT EXISTS idx_failed_jobs_timestamp ON failed_jobs(timestamp);
CREATE INDEX IF NOT EXISTS idx_failed_jobs_project ON failed_jobs(project);
CREATE INDEX IF NOT EXISTS idx_failed_jobs_failed_task ON failed_jobs(failed_task);
```

**Automated PostgreSQL Setup**: Use the provided Python script for easier setup:
```bash
python scripts/setup_postgresql_database.py \
    --host 10.0.0.14 \
    --port 5432 \
    --user postgres \
    --password your_password \
    --database ansible_execution_results
```

## MySQL Setup

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS ansible_execution_results;

USE ansible_execution_results;

-- Create success_jobs table
CREATE TABLE IF NOT EXISTS success_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    hostname VARCHAR(255),
    inventory_hostname VARCHAR(255),
    ansible_host VARCHAR(255),
    project VARCHAR(255),
    organization VARCHAR(255),
    job_template VARCHAR(255),
    playbook VARCHAR(255),
    scm_url TEXT,
    scm_branch VARCHAR(255),
    scm_revision VARCHAR(255),
    execution_environment VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    return_code INT,
    message TEXT,
    stdout TEXT,
    stderr TEXT,
    exception TEXT,
    warnings TEXT,
    failed_task VARCHAR(500),
    failed_task_module VARCHAR(255),
    os_distribution VARCHAR(100),
    os_version VARCHAR(100),
    os_family VARCHAR(100),
    os_system VARCHAR(100),
    os_architecture VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create failed_jobs table
CREATE TABLE IF NOT EXISTS failed_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    hostname VARCHAR(255),
    inventory_hostname VARCHAR(255),
    ansible_host VARCHAR(255),
    project VARCHAR(255),
    organization VARCHAR(255),
    job_template VARCHAR(255),
    playbook VARCHAR(255),
    scm_url TEXT,
    scm_branch VARCHAR(255),
    scm_revision VARCHAR(255),
    execution_environment VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    return_code INT,
    message TEXT,
    stdout TEXT,
    stderr TEXT,
    exception TEXT,
    warnings TEXT,
    failed_task VARCHAR(500),
    failed_task_module VARCHAR(255),
    os_distribution VARCHAR(100),
    os_version VARCHAR(100),
    os_family VARCHAR(100),
    os_system VARCHAR(100),
    os_architecture VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create indexes for success_jobs
CREATE INDEX idx_success_jobs_timestamp ON success_jobs(timestamp);
CREATE INDEX idx_success_jobs_project ON success_jobs(project);
CREATE INDEX idx_success_jobs_playbook ON success_jobs(playbook);
CREATE INDEX idx_success_jobs_organization ON success_jobs(organization);

-- Create indexes for failed_jobs
CREATE INDEX idx_failed_jobs_timestamp ON failed_jobs(timestamp);
CREATE INDEX idx_failed_jobs_project ON failed_jobs(project);
CREATE INDEX idx_failed_jobs_failed_task ON failed_jobs(failed_task);
```

## SQLite Setup

For SQLite, create the database file and tables:

```sql
-- Create success_jobs table
CREATE TABLE IF NOT EXISTS success_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    hostname TEXT,
    inventory_hostname TEXT,
    ansible_host TEXT,
    project TEXT,
    organization TEXT,
    job_template TEXT,
    playbook TEXT,
    scm_url TEXT,
    scm_branch TEXT,
    scm_revision TEXT,
    execution_environment TEXT,
    status TEXT NOT NULL,
    return_code INTEGER,
    message TEXT,
    stdout TEXT,
    stderr TEXT,
    exception TEXT,
    warnings TEXT,
    failed_task TEXT,
    failed_task_module TEXT,
    os_distribution TEXT,
    os_version TEXT,
    os_family TEXT,
    os_system TEXT,
    os_architecture TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create failed_jobs table
CREATE TABLE IF NOT EXISTS failed_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    hostname TEXT,
    inventory_hostname TEXT,
    ansible_host TEXT,
    project TEXT,
    organization TEXT,
    job_template TEXT,
    playbook TEXT,
    scm_url TEXT,
    scm_branch TEXT,
    scm_revision TEXT,
    execution_environment TEXT,
    status TEXT NOT NULL,
    return_code INTEGER,
    message TEXT,
    stdout TEXT,
    stderr TEXT,
    exception TEXT,
    warnings TEXT,
    failed_task TEXT,
    failed_task_module TEXT,
    os_distribution TEXT,
    os_version TEXT,
    os_family TEXT,
    os_system TEXT,
    os_architecture TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for success_jobs
CREATE INDEX IF NOT EXISTS idx_success_jobs_timestamp ON success_jobs(timestamp);
CREATE INDEX IF NOT EXISTS idx_success_jobs_project ON success_jobs(project);
CREATE INDEX IF NOT EXISTS idx_success_jobs_playbook ON success_jobs(playbook);

-- Create indexes for failed_jobs
CREATE INDEX IF NOT EXISTS idx_failed_jobs_timestamp ON failed_jobs(timestamp);
CREATE INDEX IF NOT EXISTS idx_failed_jobs_project ON failed_jobs(project);
CREATE INDEX IF NOT EXISTS idx_failed_jobs_failed_task ON failed_jobs(failed_task);
```

Create the database file:
```bash
sqlite3 /path/to/ansible_execution_results.db < schema.sql
```

## MongoDB Setup

For MongoDB, create the database and collections with validation:

```javascript
// Create database
use ansible_execution_results

// Create success_jobs collection with validation
db.createCollection("success_jobs", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["timestamp", "status"],
         properties: {
            timestamp: { bsonType: "date" },
            hostname: { bsonType: "string" },
            inventory_hostname: { bsonType: "string" },
            ansible_host: { bsonType: "string" },
            project: { bsonType: "string" },
            organization: { bsonType: "string" },
            job_template: { bsonType: "string" },
            playbook: { bsonType: "string" },
            status: { bsonType: "string" },
            return_code: { bsonType: "int" }
         }
      }
   }
})

// Create failed_jobs collection with validation
db.createCollection("failed_jobs", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["timestamp", "status"],
         properties: {
            timestamp: { bsonType: "date" },
            hostname: { bsonType: "string" },
            inventory_hostname: { bsonType: "string" },
            ansible_host: { bsonType: "string" },
            project: { bsonType: "string" },
            organization: { bsonType: "string" },
            job_template: { bsonType: "string" },
            playbook: { bsonType: "string" },
            status: { bsonType: "string" },
            return_code: { bsonType: "int" },
            failed_task: { bsonType: "string" }
         }
      }
   }
})

// Create indexes for success_jobs
db.success_jobs.createIndex({ "timestamp": 1 })
db.success_jobs.createIndex({ "project": 1 })
db.success_jobs.createIndex({ "organization": 1 })
db.success_jobs.createIndex({ "playbook": 1 })

// Create indexes for failed_jobs
db.failed_jobs.createIndex({ "timestamp": 1 })
db.failed_jobs.createIndex({ "project": 1 })
db.failed_jobs.createIndex({ "failed_task": 1 })
```

## Next Steps

After setting up your database and tables, proceed with the role configuration:
- See the main [README.md](../README.md) for usage examples
- Configure database connection variables in your playbook
- The role will automatically verify database and table existence before inserting records
