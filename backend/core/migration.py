"""
Database migration system for moving from SQLite to PostgreSQL
Provides tools for schema versioning and data migration
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger


class MigrationManager:
    """
    Manage database schema versioning and migrations

    Supports:
    - Schema version tracking
    - Forward migrations (SQLite → PostgreSQL)
    - Rollback capabilities
    - Data export/import
    """

    def __init__(
        self,
        sqlite_path: str = "backend/data/vbs.db",
        migrations_dir: str = "backend/migrations"
    ):
        self.sqlite_path = Path(sqlite_path)
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(parents=True, exist_ok=True)

        # Migration history tracking
        self.migration_history_path = self.migrations_dir / "migration_history.json"

    def get_current_schema_version(self) -> int:
        """
        Get current schema version from database

        Returns:
            Schema version number (0 if not tracked)
        """
        try:
            if not self.sqlite_path.exists():
                return 0

            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()

            # Check if schema_version table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='schema_version'
            """)

            if not cursor.fetchone():
                # Schema version not tracked yet
                conn.close()
                return 0

            # Get current version
            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            result = cursor.fetchone()
            conn.close()

            return result[0] if result else 0

        except Exception as e:
            logger.error(f"Failed to get schema version: {e}")
            return 0

    def set_schema_version(self, version: int):
        """
        Set schema version in database

        Args:
            version: Schema version number
        """
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()

            # Create schema_version table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            """)

            # Insert version
            cursor.execute("""
                INSERT INTO schema_version (version, applied_at)
                VALUES (?, ?)
            """, (version, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            logger.info(f"Schema version set to {version}")

        except Exception as e:
            logger.error(f"Failed to set schema version: {e}")

    def export_schema(self) -> Dict[str, Any]:
        """
        Export current SQLite schema

        Returns:
            Schema definition with CREATE statements
        """
        try:
            if not self.sqlite_path.exists():
                return {'error': 'Database not found'}

            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("""
                SELECT name, sql FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            tables = {}
            for table_name, create_sql in cursor.fetchall():
                tables[table_name] = {
                    'create_sql': create_sql,
                    'columns': []
                }

                # Get column information
                # SECURITY FIX: Quote identifier (table_name from sqlite_master is safe, but quote anyway)
                cursor.execute(f'PRAGMA table_info("{table_name}")')
                for col_info in cursor.fetchall():
                    tables[table_name]['columns'].append({
                        'name': col_info[1],
                        'type': col_info[2],
                        'not_null': bool(col_info[3]),
                        'default_value': col_info[4],
                        'primary_key': bool(col_info[5])
                    })

            # Get indexes
            cursor.execute("""
                SELECT name, sql FROM sqlite_master
                WHERE type='index' AND sql IS NOT NULL
                ORDER BY name
            """)

            indexes = {}
            for index_name, create_sql in cursor.fetchall():
                indexes[index_name] = create_sql

            conn.close()

            return {
                'database_type': 'sqlite',
                'version': self.get_current_schema_version(),
                'tables': tables,
                'indexes': indexes,
                'exported_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to export schema: {e}")
            return {'error': str(e)}

    def generate_postgresql_schema(self) -> str:
        """
        Generate PostgreSQL-compatible schema from SQLite

        Returns:
            PostgreSQL CREATE statements
        """
        schema = self.export_schema()

        if 'error' in schema:
            return f"-- Error: {schema['error']}"

        postgresql_sql = []
        postgresql_sql.append("-- PostgreSQL Schema")
        postgresql_sql.append(f"-- Generated from SQLite on {datetime.now().isoformat()}")
        postgresql_sql.append(f"-- Schema version: {schema['version']}\n")

        # Type mapping from SQLite to PostgreSQL
        type_mapping = {
            'INTEGER': 'INTEGER',
            'TEXT': 'TEXT',
            'REAL': 'REAL',
            'BLOB': 'BYTEA',
            'NUMERIC': 'NUMERIC',
            'BOOLEAN': 'BOOLEAN',
            'DATETIME': 'TIMESTAMP',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'VARCHAR': 'VARCHAR',
            'FLOAT': 'DOUBLE PRECISION',
            'JSON': 'JSONB'
        }

        # Convert tables
        for table_name, table_info in schema['tables'].items():
            postgresql_sql.append(f"-- Table: {table_name}")

            # Start CREATE TABLE
            create_parts = [f"CREATE TABLE {table_name} ("]

            column_defs = []
            for col in table_info['columns']:
                # Map SQLite type to PostgreSQL
                col_type = col['type'].upper()
                pg_type = type_mapping.get(col_type, col_type)

                # Build column definition
                col_def = f"    {col['name']} {pg_type}"

                if col['primary_key']:
                    col_def += " PRIMARY KEY"

                if col['not_null'] and not col['primary_key']:
                    col_def += " NOT NULL"

                if col['default_value'] is not None:
                    col_def += f" DEFAULT {col['default_value']}"

                column_defs.append(col_def)

            create_parts.append(",\n".join(column_defs))
            create_parts.append(");\n")

            postgresql_sql.append("".join(create_parts))

        # Convert indexes
        if schema.get('indexes'):
            postgresql_sql.append("\n-- Indexes")
            for index_name, index_sql in schema['indexes'].items():
                # SQLite and PostgreSQL index syntax is similar
                postgresql_sql.append(f"{index_sql};\n")

        return "\n".join(postgresql_sql)

    def save_migration(self, name: str, migration_sql: str) -> Path:
        """
        Save migration SQL to file

        Args:
            name: Migration name
            migration_sql: SQL statements

        Returns:
            Path to saved migration file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.sql"
        filepath = self.migrations_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(migration_sql)

        logger.info(f"Migration saved: {filename}")
        return filepath

    def list_migrations(self) -> List[Dict[str, Any]]:
        """
        List all available migrations

        Returns:
            List of migration metadata
        """
        migrations = []

        for file in sorted(self.migrations_dir.glob("*.sql")):
            migrations.append({
                'filename': file.name,
                'path': str(file),
                'size_bytes': file.stat().st_size,
                'created': datetime.fromtimestamp(file.stat().st_ctime).isoformat()
            })

        return migrations

    def record_migration_history(self, migration_name: str, status: str, details: Optional[Dict] = None):
        """
        Record migration in history

        Args:
            migration_name: Name of migration
            status: Status (success, failed, rolled_back)
            details: Additional details
        """
        history = []

        # Load existing history
        if self.migration_history_path.exists():
            with open(self.migration_history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)

        # Add new entry
        entry = {
            'migration': migration_name,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }

        if details:
            entry['details'] = details

        history.append(entry)

        # Save updated history
        with open(self.migration_history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)

        logger.info(f"Migration history recorded: {migration_name} - {status}")

    def get_migration_guide(self) -> Dict[str, Any]:
        """
        Get step-by-step migration guide from SQLite to PostgreSQL

        Returns:
            Migration guide with instructions
        """
        return {
            'title': 'SQLite to PostgreSQL Migration Guide',
            'current_version': self.get_current_schema_version(),
            'steps': [
                {
                    'step': 1,
                    'title': 'Backup Current Database',
                    'command': 'POST /admin/backup/create',
                    'description': 'Create full backup of SQLite database before migration'
                },
                {
                    'step': 2,
                    'title': 'Export Schema',
                    'command': 'python -m backend.core.migration export_schema',
                    'description': 'Export current SQLite schema'
                },
                {
                    'step': 3,
                    'title': 'Generate PostgreSQL Schema',
                    'command': 'python -m backend.core.migration generate_postgresql',
                    'description': 'Convert SQLite schema to PostgreSQL'
                },
                {
                    'step': 4,
                    'title': 'Setup PostgreSQL Database',
                    'description': 'Install PostgreSQL and create database'
                },
                {
                    'step': 5,
                    'title': 'Apply Schema to PostgreSQL',
                    'command': 'psql -d vintedbot < migrations/postgresql_schema.sql',
                    'description': 'Create tables and indexes in PostgreSQL'
                },
                {
                    'step': 6,
                    'title': 'Export Data from SQLite',
                    'command': 'POST /admin/export (format=json)',
                    'description': 'Export all data to JSON format'
                },
                {
                    'step': 7,
                    'title': 'Import Data to PostgreSQL',
                    'description': 'Use custom import script to load JSON into PostgreSQL'
                },
                {
                    'step': 8,
                    'title': 'Update Connection String',
                    'description': 'Update DATABASE_URL in .env to PostgreSQL connection string'
                },
                {
                    'step': 9,
                    'title': 'Test Migration',
                    'description': 'Verify all data migrated correctly, test all features'
                },
                {
                    'step': 10,
                    'title': 'Switch to PostgreSQL',
                    'description': 'Deploy with PostgreSQL as primary database'
                }
            ],
            'notes': [
                'Expect 1-2 hours downtime for migration',
                'Test thoroughly in staging environment first',
                'Keep SQLite backup for 30 days after migration',
                'Monitor PostgreSQL performance after migration'
            ],
            'estimated_downtime': '1-2 hours',
            'difficulty': 'Intermediate'
        }


# CLI interface for migration tools
if __name__ == "__main__":
    import sys

    manager = MigrationManager()

    if len(sys.argv) < 2:
        print("Usage: python -m backend.core.migration <command>")
        print("Commands:")
        print("  export_schema       - Export SQLite schema")
        print("  generate_postgresql - Generate PostgreSQL schema")
        print("  migration_guide     - Show migration guide")
        sys.exit(1)

    command = sys.argv[1]

    if command == "export_schema":
        schema = manager.export_schema()
        output_file = "backend/migrations/sqlite_schema.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        print(f"Schema exported to {output_file}")

    elif command == "generate_postgresql":
        pg_schema = manager.generate_postgresql_schema()
        output_file = "backend/migrations/postgresql_schema.sql"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pg_schema)
        print(f"PostgreSQL schema generated: {output_file}")

    elif command == "migration_guide":
        guide = manager.get_migration_guide()
        print(f"\n{guide['title']}")
        print("=" * 60)
        print(f"Current Schema Version: {guide['current_version']}")
        print(f"Estimated Downtime: {guide['estimated_downtime']}")
        print(f"Difficulty: {guide['difficulty']}\n")

        for step in guide['steps']:
            print(f"Step {step['step']}: {step['title']}")
            print(f"  {step['description']}")
            if 'command' in step:
                print(f"  Command: {step['command']}")
            print()

        print("Important Notes:")
        for note in guide['notes']:
            print(f"  - {note}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
