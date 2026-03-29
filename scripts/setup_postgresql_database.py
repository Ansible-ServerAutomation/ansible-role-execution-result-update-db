#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script for ansible-role-execution-result-update-db

This script initializes the PostgreSQL database and creates the required tables
for storing Ansible execution results.

Usage:
    python setup_postgresql_database.py --host <host> --port <port> --username <user> --password <pass> [options]

Example:
    python setup_postgresql_database.py --host localhost --port 5432 --username postgres --password mypass
    python setup_postgresql_database.py --host 10.0.0.14 --username postgres --password secret --dry-run
"""

import argparse
import sys

try:
    import psycopg2
    from psycopg2 import OperationalError, DatabaseError
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("ERROR: psycopg2 module not found.")
    print("Please install it using: pip install psycopg2-binary")
    sys.exit(1)


# Default configuration values (matching defaults/main.yml)
DEFAULT_DATABASE = "ansible_execution_results"
DEFAULT_TABLE_SUCCESS = "success_jobs"
DEFAULT_TABLE_FAILED = "failed_jobs"
DEFAULT_PORT = 5432


# SQL DDL Templates (from vars/main.yml)
def get_success_table_ddl(table_name):
    """Generate CREATE TABLE statement for success_jobs table."""
    return f"""
CREATE TABLE IF NOT EXISTS {table_name} (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL,
  hostname VARCHAR(255),
  inventory_hostname VARCHAR(255),
  ansible_host VARCHAR(255),
  project VARCHAR(500),
  organization VARCHAR(500),
  job_template VARCHAR(500),
  playbook VARCHAR(500),
  scm_url VARCHAR(1000),
  scm_branch VARCHAR(255),
  scm_revision VARCHAR(255),
  execution_environment VARCHAR(500),
  status VARCHAR(50) NOT NULL,
  return_code INTEGER,
  message TEXT,
  stdout TEXT,
  stderr TEXT,
  exception TEXT,
  warnings JSONB,
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
"""


def get_success_table_indexes(table_name):
    """Generate CREATE INDEX statements for success_jobs table."""
    return [
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp);",
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_project ON {table_name}(project);",
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_playbook ON {table_name}(playbook);"
    ]


def get_failed_table_ddl(table_name):
    """Generate CREATE TABLE statement for failed_jobs table."""
    return f"""
CREATE TABLE IF NOT EXISTS {table_name} (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL,
  hostname VARCHAR(255),
  inventory_hostname VARCHAR(255),
  ansible_host VARCHAR(255),
  project VARCHAR(500),
  organization VARCHAR(500),
  job_template VARCHAR(500),
  playbook VARCHAR(500),
  scm_url VARCHAR(1000),
  scm_branch VARCHAR(255),
  scm_revision VARCHAR(255),
  execution_environment VARCHAR(500),
  status VARCHAR(50) NOT NULL,
  return_code INTEGER,
  message TEXT,
  stdout TEXT,
  stderr TEXT,
  exception TEXT,
  warnings JSONB,
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
"""


def get_failed_table_indexes(table_name):
    """Generate CREATE INDEX statements for failed_jobs table."""
    return [
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp);",
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_project ON {table_name}(project);",
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_failed_task ON {table_name}(failed_task);"
    ]


def check_database_exists(cursor, database_name):
    """
    Check if a database exists.
    
    Args:
        cursor: PostgreSQL cursor object
        database_name (str): Name of the database to check
        
    Returns:
        bool: True if database exists, False otherwise
    """
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (database_name,)
    )
    return cursor.fetchone() is not None


def create_database(host, port, username, password, database_name, ssl_mode=None, dry_run=False):
    """
    Create PostgreSQL database if it doesn't exist.
    
    Args:
        host (str): PostgreSQL server hostname
        port (int): PostgreSQL server port
        username (str): Database username
        password (str): Database password
        database_name (str): Name of database to create
        ssl_mode (str): SSL mode (disable, allow, prefer, require, verify-ca, verify-full)
        dry_run (bool): If True, only show what would be done
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print("STEP 1: Database Creation")
    print(f"{'='*70}")
    
    if dry_run:
        print(f"[DRY RUN] Would create database: {database_name}")
        print(f"[DRY RUN] SQL: CREATE DATABASE {database_name};")
        return True
    
    try:
        # Connect to default 'postgres' database to create target database
        ssl_params = {}
        if ssl_mode:
            ssl_params['sslmode'] = ssl_mode
            
        connection = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database='postgres',
            connect_timeout=10,
            **ssl_params
        )
        
        # Set autocommit mode for database creation
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        
        # Check if database exists
        if check_database_exists(cursor, database_name):
            print(f"✓ Database '{database_name}' already exists (skipped)")
        else:
            print(f"Creating database '{database_name}'...")
            cursor.execute(f"CREATE DATABASE {database_name};")
            print(f"✓ Database '{database_name}' created successfully")
        
        cursor.close()
        connection.close()
        return True
        
    except OperationalError as e:
        print(f"✗ Connection failed: {e}")
        return False
    except DatabaseError as e:
        print(f"✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def create_tables(host, port, username, password, database_name, 
                 table_success, table_failed, ssl_mode=None, 
                 drop_tables=False, dry_run=False):
    """
    Create tables and indexes in the target database.
    
    Args:
        host (str): PostgreSQL server hostname
        port (int): PostgreSQL server port
        username (str): Database username
        password (str): Database password
        database_name (str): Target database name
        table_success (str): Name for success_jobs table
        table_failed (str): Name for failed_jobs table
        ssl_mode (str): SSL mode
        drop_tables (bool): If True, drop existing tables before creating
        dry_run (bool): If True, only show what would be done
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print("STEP 2: Table and Index Creation")
    print(f"{'='*70}")
    
    # Generate DDL statements
    success_ddl = get_success_table_ddl(table_success)
    success_indexes = get_success_table_indexes(table_success)
    failed_ddl = get_failed_table_ddl(table_failed)
    failed_indexes = get_failed_table_indexes(table_failed)
    
    if dry_run:
        print(f"\n[DRY RUN] Would execute on database '{database_name}':\n")
        
        if drop_tables:
            print(f"-- Drop existing tables")
            print(f"DROP TABLE IF EXISTS {table_success} CASCADE;")
            print(f"DROP TABLE IF EXISTS {table_failed} CASCADE;\n")
        
        print(f"-- Create success_jobs table")
        print(success_ddl)
        
        print(f"\n-- Create indexes for success_jobs")
        for idx_sql in success_indexes:
            print(idx_sql)
        
        print(f"\n-- Create failed_jobs table")
        print(failed_ddl)
        
        print(f"\n-- Create indexes for failed_jobs")
        for idx_sql in failed_indexes:
            print(idx_sql)
        
        return True
    
    try:
        # Connect to target database
        ssl_params = {}
        if ssl_mode:
            ssl_params['sslmode'] = ssl_mode
            
        connection = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connect_timeout=10,
            **ssl_params
        )
        
        cursor = connection.cursor()
        
        # Drop tables if requested
        if drop_tables:
            print(f"\nDropping existing tables (if they exist)...")
            cursor.execute(f"DROP TABLE IF EXISTS {table_success} CASCADE;")
            cursor.execute(f"DROP TABLE IF EXISTS {table_failed} CASCADE;")
            connection.commit()
            print(f"✓ Existing tables dropped")
        
        # Create success_jobs table
        print(f"\nCreating table '{table_success}'...")
        cursor.execute(success_ddl)
        connection.commit()
        print(f"✓ Table '{table_success}' created")
        
        # Create indexes for success_jobs
        print(f"Creating indexes for '{table_success}'...")
        for idx_sql in success_indexes:
            cursor.execute(idx_sql)
        connection.commit()
        print(f"✓ Indexes created for '{table_success}'")
        
        # Create failed_jobs table
        print(f"\nCreating table '{table_failed}'...")
        cursor.execute(failed_ddl)
        connection.commit()
        print(f"✓ Table '{table_failed}' created")
        
        # Create indexes for failed_jobs
        print(f"Creating indexes for '{table_failed}'...")
        for idx_sql in failed_indexes:
            cursor.execute(idx_sql)
        connection.commit()
        print(f"✓ Indexes created for '{table_failed}'")
        
        # Get table information
        cursor.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_name IN (%s, %s)
            ORDER BY table_name;
        """, (table_success, table_failed))
        
        tables_info = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        # Display summary
        print(f"\n{'='*70}")
        print("Table Summary")
        print(f"{'='*70}")
        for table_name, col_count in tables_info:
            print(f"  {table_name}: {col_count} columns")
        
        return True
        
    except OperationalError as e:
        print(f"✗ Connection failed: {e}")
        return False
    except DatabaseError as e:
        print(f"✗ Database error: {e}")
        if connection:
            connection.rollback()
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if connection:
            connection.rollback()
        return False


def verify_setup(host, port, username, password, database_name, 
                table_success, table_failed, ssl_mode=None):
    """
    Verify the database setup by checking tables and indexes.
    
    Args:
        host (str): PostgreSQL server hostname
        port (int): PostgreSQL server port
        username (str): Database username
        password (str): Database password
        database_name (str): Target database name
        table_success (str): Name for success_jobs table
        table_failed (str): Name for failed_jobs table
        ssl_mode (str): SSL mode
        
    Returns:
        bool: True if verification passed, False otherwise
    """
    print(f"\n{'='*70}")
    print("STEP 3: Verification")
    print(f"{'='*70}")
    
    try:
        ssl_params = {}
        if ssl_mode:
            ssl_params['sslmode'] = ssl_mode
            
        connection = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connect_timeout=10,
            **ssl_params
        )
        
        cursor = connection.cursor()
        
        # Check tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (%s, %s)
            ORDER BY table_name;
        """, (table_success, table_failed))
        
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\nTables found: {len(tables)}")
        for table in tables:
            print(f"  ✓ {table}")
        
        # Check indexes
        cursor.execute("""
            SELECT tablename, indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN (%s, %s)
            ORDER BY tablename, indexname;
        """, (table_success, table_failed))
        
        indexes = cursor.fetchall()
        
        print(f"\nIndexes found: {len(indexes)}")
        for table, index in indexes:
            print(f"  ✓ {table}.{index}")
        
        cursor.close()
        connection.close()
        
        # Verify expected tables exist
        expected_tables = {table_success, table_failed}
        if set(tables) == expected_tables:
            print(f"\n✓ Verification PASSED - All required tables exist")
            return True
        else:
            missing = expected_tables - set(tables)
            print(f"\n✗ Verification FAILED - Missing tables: {missing}")
            return False
        
    except Exception as e:
        print(f"✗ Verification error: {e}")
        return False


def main():
    """Main function to parse arguments and setup PostgreSQL database."""
    parser = argparse.ArgumentParser(
        description='Setup PostgreSQL database and tables for ansible-role-execution-result-update-db',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic setup with defaults
  python %(prog)s --host localhost --username postgres --password mypass
  
  # Setup with custom database and table names
  python %(prog)s --host 10.0.0.14 --username dbadmin --password secret \\
    --database my_ansible_db --table-success my_success --table-failed my_failed
  
  # Dry-run to preview SQL statements
  python %(prog)s --host localhost --username postgres --password mypass --dry-run
  
  # Drop and recreate tables
  python %(prog)s --host localhost --username postgres --password mypass --drop-tables
  
  # Use SSL connection
  python %(prog)s --host db.example.com --username postgres --password mypass \\
    --ssl-mode require
        '''
    )
    
    # Connection parameters
    parser.add_argument(
        '--host', '-H',
        required=True,
        help='PostgreSQL server IP address or hostname'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=DEFAULT_PORT,
        help=f'PostgreSQL server port number (default: {DEFAULT_PORT})'
    )
    
    parser.add_argument(
        '--username', '-u',
        required=True,
        help='Database username (must have CREATE DATABASE privileges)'
    )
    
    parser.add_argument(
        '--password', '-P',
        required=True,
        help='Database password'
    )
    
    # Database and table names
    parser.add_argument(
        '--database', '-d',
        default=DEFAULT_DATABASE,
        help=f'Database name to create (default: {DEFAULT_DATABASE})'
    )
    
    parser.add_argument(
        '--table-success',
        default=DEFAULT_TABLE_SUCCESS,
        help=f'Table name for successful executions (default: {DEFAULT_TABLE_SUCCESS})'
    )
    
    parser.add_argument(
        '--table-failed',
        default=DEFAULT_TABLE_FAILED,
        help=f'Table name for failed executions (default: {DEFAULT_TABLE_FAILED})'
    )
    
    # SSL/TLS options
    parser.add_argument(
        '--ssl-mode',
        choices=['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full'],
        help='SSL mode for connection (default: prefer)'
    )
    
    # Operation modes
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview SQL statements without executing them'
    )
    
    parser.add_argument(
        '--drop-tables',
        action='store_true',
        help='Drop existing tables before creating (WARNING: destroys data!)'
    )
    
    parser.add_argument(
        '--skip-verification',
        action='store_true',
        help='Skip verification step after creation'
    )
    
    args = parser.parse_args()
    
    # Display configuration
    print(f"\n{'='*70}")
    print("PostgreSQL Database Setup for ansible-role-execution-result-update-db")
    print(f"{'='*70}")
    print(f"Host:                 {args.host}")
    print(f"Port:                 {args.port}")
    print(f"Username:             {args.username}")
    print(f"Database:             {args.database}")
    print(f"Success Table:        {args.table_success}")
    print(f"Failed Table:         {args.table_failed}")
    print(f"SSL Mode:             {args.ssl_mode or 'prefer (default)'}")
    print(f"Mode:                 {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    if args.drop_tables:
        print(f"WARNING:              Will drop existing tables!")
    print(f"{'='*70}")
    
    # Confirm if dropping tables
    if args.drop_tables and not args.dry_run:
        response = input("\n⚠️  WARNING: This will DROP existing tables and ALL data! Continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Aborted.")
            sys.exit(0)
    
    # Step 1: Create database
    success = create_database(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        database_name=args.database,
        ssl_mode=args.ssl_mode,
        dry_run=args.dry_run
    )
    
    if not success:
        print(f"\n{'='*70}")
        print("Status: FAILED at database creation")
        print(f"{'='*70}\n")
        sys.exit(1)
    
    # Step 2: Create tables and indexes
    success = create_tables(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        database_name=args.database,
        table_success=args.table_success,
        table_failed=args.table_failed,
        ssl_mode=args.ssl_mode,
        drop_tables=args.drop_tables,
        dry_run=args.dry_run
    )
    
    if not success:
        print(f"\n{'='*70}")
        print("Status: FAILED at table creation")
        print(f"{'='*70}\n")
        sys.exit(1)
    
    # Step 3: Verify setup (skip in dry-run mode)
    if not args.dry_run and not args.skip_verification:
        success = verify_setup(
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            database_name=args.database,
            table_success=args.table_success,
            table_failed=args.table_failed,
            ssl_mode=args.ssl_mode
        )
        
        if not success:
            print(f"\n{'='*70}")
            print("Status: FAILED at verification")
            print(f"{'='*70}\n")
            sys.exit(1)
    
    # Success summary
    print(f"\n{'='*70}")
    if args.dry_run:
        print("Status: DRY RUN COMPLETE - No changes made")
    else:
        print("Status: SUCCESS - Database setup completed successfully!")
    print(f"{'='*70}")
    
    if not args.dry_run:
        print(f"\nDatabase '{args.database}' is ready to receive Ansible execution results.")
        print(f"Tables created: {args.table_success}, {args.table_failed}")
        print(f"\nYou can now configure your Ansible role with:")
        print(f"  execution_result_db_host: {args.host}")
        print(f"  execution_result_db_port: {args.port}")
        print(f"  execution_result_db_name: {args.database}")
        print(f"  execution_result_db_table_success: {args.table_success}")
        print(f"  execution_result_db_table_failed: {args.table_failed}")
    
    print()


if __name__ == "__main__":
    main()
