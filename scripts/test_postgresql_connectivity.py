#!/usr/bin/env python3
"""
PostgreSQL Connectivity Test Script

This script tests the connectivity to a PostgreSQL database server.
Usage:
    python test_postgresql_connectivity.py --host <host> --port <port> --username <user> --password <pass> [--database <db>]

Example:
    python test_postgresql_connectivity.py --host 10.0.0.14 --port 5432 --username postgres --password mypass --database testdb
"""

import argparse
import sys

try:
    import psycopg2
    from psycopg2 import OperationalError, DatabaseError
except ImportError:
    print("ERROR: psycopg2 module not found.")
    print("Please install it using: pip install psycopg2-binary")
    sys.exit(1)


def test_postgresql_connection(host, port, username, password, database='postgres'):
    """
    Test PostgreSQL database connectivity.
    
    Args:
        host (str): PostgreSQL server IP address or hostname
        port (int): PostgreSQL server port number
        username (str): Database username
        password (str): Database password
        database (str): Database name (default: 'postgres')
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    print(f"\n{'='*60}")
    print("PostgreSQL Connectivity Test")
    print(f"{'='*60}")
    print(f"Host:     {host}")
    print(f"Port:     {port}")
    print(f"Username: {username}")
    print(f"Database: {database}")
    print(f"{'='*60}\n")
    
    try:
        # Attempt to establish connection
        print("Attempting to connect to PostgreSQL server...")
        connection = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            connect_timeout=10
        )
        
        # Create a cursor to execute queries
        cursor = connection.cursor()
        
        # Test query to verify connection
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print("✓ Connection successful!")
        print(f"\nPostgreSQL Version:\n{db_version[0]}")
        
        # Get additional server information
        cursor.execute("SELECT current_database(), current_user;")
        db_info = cursor.fetchone()
        print(f"\nConnected to database: {db_info[0]}")
        print(f"Connected as user: {db_info[1]}")
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        print(f"\n{'='*60}")
        print("Status: SUCCESS - All connectivity tests passed!")
        print(f"{'='*60}\n")
        
        return True
        
    except OperationalError as e:
        print("✗ Connection failed!")
        print(f"\nOperational Error: {e}")
        print("\nPossible causes:")
        print("  - PostgreSQL server is not running")
        print("  - Incorrect host/port configuration")
        print("  - Network connectivity issues")
        print("  - Firewall blocking the connection")
        print(f"\n{'='*60}")
        print("Status: FAILED")
        print(f"{'='*60}\n")
        return False
        
    except DatabaseError as e:
        print("✗ Database error occurred!")
        print(f"\nDatabase Error: {e}")
        print("\nPossible causes:")
        print("  - Invalid credentials (username/password)")
        print("  - Database does not exist")
        print("  - Insufficient privileges")
        print(f"\n{'='*60}")
        print("Status: FAILED")
        print(f"{'='*60}\n")
        return False
        
    except Exception as e:
        print("✗ Unexpected error occurred!")
        print(f"\nError: {e}")
        print(f"\n{'='*60}")
        print("Status: FAILED")
        print(f"{'='*60}\n")
        return False


def main():
    """Main function to parse arguments and test connection."""
    parser = argparse.ArgumentParser(
        description='Test PostgreSQL database connectivity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Test connection to PostgreSQL server at 10.0.0.14
  python %(prog)s --host 10.0.0.14 --port 5432 --username postgres --password mypass
  
  # Test connection to a specific database
  python %(prog)s --host 10.0.0.14 --port 5432 --username dbuser --password secret --database mydb
        '''
    )
    
    parser.add_argument(
        '--host', '-H',
        required=True,
        help='PostgreSQL server IP address or hostname (e.g., 10.0.0.14)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5432,
        help='PostgreSQL server port number (default: 5432)'
    )
    
    parser.add_argument(
        '--username', '-u',
        required=True,
        help='Database username'
    )
    
    parser.add_argument(
        '--password', '-P',
        required=True,
        help='Database password'
    )
    
    parser.add_argument(
        '--database', '-d',
        default='postgres',
        help='Database name to connect to (default: postgres)'
    )
    
    args = parser.parse_args()
    
    # Test the connection
    success = test_postgresql_connection(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        database=args.database
    )
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
