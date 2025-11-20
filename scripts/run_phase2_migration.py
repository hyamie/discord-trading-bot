#!/usr/bin/env python3
"""
Phase II Database Migration Script
Applies the phase2_migration.sql to the Supabase database
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_file = project_root / '.env.supabase'
if env_file.exists():
    load_dotenv(env_file)
else:
    print("❌ .env.supabase file not found!")
    sys.exit(1)

def run_migration():
    """Execute the Phase II migration SQL"""

    # Get database connection details
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("[ERROR] DATABASE_URL not found in environment!")
        sys.exit(1)

    # Read migration SQL
    migration_file = project_root / 'database' / 'phase2_migration.sql'
    if not migration_file.exists():
        print(f"[ERROR] Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    print("=" * 60)
    print("Phase II Database Migration")
    print("=" * 60)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    print(f"Schema: discord_trading")
    print(f"Migration file: {migration_file.name}")
    print("=" * 60)

    # Connect and execute
    try:
        print("\n[*] Connecting to database...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Set schema
        print("[*] Setting schema to discord_trading...")
        cursor.execute("SET search_path TO discord_trading, public;")

        # Execute migration
        print("[*] Executing migration SQL...")
        cursor.execute(migration_sql)

        # Verify tables created
        print("\n[SUCCESS] Migration executed successfully!")
        print("\n[*] Verifying new tables...")

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'discord_trading'
            AND table_name IN ('trade_signals', 'weekly_reports')
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        if tables:
            print("   Created tables:")
            for (table,) in tables:
                print(f"     [+] {table}")

        # Verify materialized view
        cursor.execute("""
            SELECT matviewname
            FROM pg_matviews
            WHERE schemaname = 'discord_trading'
            AND matviewname = 'edge_performance';
        """)

        if cursor.fetchone():
            print("     [+] edge_performance (materialized view)")

        # Verify helper views
        cursor.execute("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'discord_trading'
            AND table_name LIKE 'v_%'
            ORDER BY table_name;
        """)

        views = cursor.fetchall()
        if views:
            print("\n   Created views:")
            for (view,) in views:
                print(f"     [+] {view}")

        print("\n" + "=" * 60)
        print("[SUCCESS] Phase II Migration Complete!")
        print("=" * 60)
        print("\nNext Steps:")
        print("  1. Create src/database/trade_logger.py")
        print("  2. Update FastAPI /analyze endpoint")
        print("  3. Create scripts/outcome_tracker.py")
        print("  4. Build Next.js dashboard")
        print("=" * 60)

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
