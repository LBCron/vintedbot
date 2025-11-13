"""
Comprehensive monitoring system for VintedBot
Tracks system health, performance, and issues
"""
import os
import psutil
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger
import sqlite3


class SystemMonitor:
    """Monitor system resources and health"""

    def __init__(self):
        self.start_time = time.time()

    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            'rss_mb': memory_info.rss / (1024 * 1024),  # Resident Set Size
            'vms_mb': memory_info.vms / (1024 * 1024),  # Virtual Memory Size
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / (1024 * 1024),
            'total_mb': psutil.virtual_memory().total / (1024 * 1024)
        }

    def get_cpu_usage(self) -> Dict[str, Any]:
        """Get CPU usage statistics"""
        process = psutil.Process()

        return {
            'percent': process.cpu_percent(interval=0.1),
            'num_threads': process.num_threads(),
            'system_percent': psutil.cpu_percent(interval=0.1),
            'cpu_count': psutil.cpu_count()
        }

    def get_disk_usage(self, path: str = ".") -> Dict[str, Any]:
        """Get disk usage for given path"""
        disk = psutil.disk_usage(path)

        return {
            'total_gb': disk.total / (1024 ** 3),
            'used_gb': disk.used / (1024 ** 3),
            'free_gb': disk.free / (1024 ** 3),
            'percent': disk.percent
        }

    def get_database_size(self, db_path: str) -> Dict[str, Any]:
        """Get SQLite database size and stats"""
        if not Path(db_path).exists():
            return {'error': 'Database not found'}

        try:
            size_bytes = Path(db_path).stat().st_size
            size_mb = size_bytes / (1024 * 1024)

            # Get table counts
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            table_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except:
                    table_counts[table] = -1

            conn.close()

            return {
                'size_mb': size_mb,
                'size_bytes': size_bytes,
                'table_counts': table_counts,
                'total_records': sum(c for c in table_counts.values() if c > 0)
            }
        except Exception as e:
            return {'error': str(e)}

    def get_directory_size(self, path: str) -> Dict[str, Any]:
        """Get total size of directory"""
        try:
            total_size = 0
            file_count = 0

            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.exists():
                        total_size += file_path.stat().st_size
                        file_count += 1

            return {
                'total_mb': total_size / (1024 * 1024),
                'total_gb': total_size / (1024 ** 3),
                'file_count': file_count
            }
        except Exception as e:
            return {'error': str(e)}


class HealthChecker:
    """Comprehensive health checking system"""

    def __init__(self):
        self.monitor = SystemMonitor()
        self.checks: List[Dict[str, Any]] = []

    async def check_database_connection(self, db_path: str) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            if not Path(db_path).exists():
                return {
                    'status': 'fail',
                    'message': 'Database file not found',
                    'details': {'path': db_path}
                }

            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()

            if result == (1,):
                return {
                    'status': 'pass',
                    'message': 'Database connection successful',
                    'details': self.monitor.get_database_size(db_path)
                }
            else:
                return {
                    'status': 'fail',
                    'message': 'Database query failed'
                }

        except Exception as e:
            return {
                'status': 'fail',
                'message': f'Database connection error: {str(e)}'
            }

    async def check_disk_space(self, min_free_gb: float = 1.0) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            disk_usage = self.monitor.get_disk_usage()

            if disk_usage['free_gb'] < min_free_gb:
                return {
                    'status': 'warn',
                    'message': f"Low disk space: {disk_usage['free_gb']:.2f} GB free",
                    'details': disk_usage
                }

            return {
                'status': 'pass',
                'message': f"Sufficient disk space: {disk_usage['free_gb']:.2f} GB free",
                'details': disk_usage
            }

        except Exception as e:
            return {
                'status': 'fail',
                'message': f'Disk check error: {str(e)}'
            }

    async def check_memory_usage(self, max_percent: float = 90.0) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = self.monitor.get_memory_usage()

            if memory['percent'] > max_percent:
                return {
                    'status': 'warn',
                    'message': f"High memory usage: {memory['percent']:.1f}%",
                    'details': memory
                }

            return {
                'status': 'pass',
                'message': f"Memory usage normal: {memory['percent']:.1f}%",
                'details': memory
            }

        except Exception as e:
            return {
                'status': 'fail',
                'message': f'Memory check error: {str(e)}'
            }

    async def check_circuit_breakers(self) -> Dict[str, Any]:
        """Check status of circuit breakers"""
        try:
            from backend.core.circuit_breaker import get_all_circuit_states

            states = get_all_circuit_states()
            open_breakers = [
                name for name, state in states.items()
                if state['state'] == 'open'
            ]

            if open_breakers:
                return {
                    'status': 'warn',
                    'message': f"Circuit breakers open: {', '.join(open_breakers)}",
                    'details': states
                }

            return {
                'status': 'pass',
                'message': 'All circuit breakers closed',
                'details': states
            }

        except Exception as e:
            return {
                'status': 'fail',
                'message': f'Circuit breaker check error: {str(e)}'
            }

    async def check_job_health(self) -> Dict[str, Any]:
        """Check health of background jobs"""
        try:
            from backend.core.job_wrapper import get_job_health

            health = get_job_health()

            if health['unhealthy_jobs'] > 0:
                return {
                    'status': 'fail',
                    'message': f"{health['unhealthy_jobs']} unhealthy job(s)",
                    'details': health
                }
            elif health['degraded_jobs'] > 0:
                return {
                    'status': 'warn',
                    'message': f"{health['degraded_jobs']} degraded job(s)",
                    'details': health
                }

            return {
                'status': 'pass',
                'message': 'All jobs healthy',
                'details': health
            }

        except Exception as e:
            return {
                'status': 'fail',
                'message': f'Job health check error: {str(e)}'
            }

    async def check_storage_quotas(self, data_dir: str = "backend/data") -> Dict[str, Any]:
        """Check storage usage for uploads, temp files, etc."""
        try:
            uploads_dir = Path(data_dir) / "uploads"
            temp_dir = Path(data_dir) / "temp_photos"

            uploads_size = self.monitor.get_directory_size(str(uploads_dir)) if uploads_dir.exists() else {'total_mb': 0}
            temp_size = self.monitor.get_directory_size(str(temp_dir)) if temp_dir.exists() else {'total_mb': 0}

            total_mb = uploads_size.get('total_mb', 0) + temp_size.get('total_mb', 0)

            return {
                'status': 'pass',
                'message': f"Storage usage: {total_mb:.2f} MB",
                'details': {
                    'uploads_mb': uploads_size.get('total_mb', 0),
                    'temp_mb': temp_size.get('total_mb', 0),
                    'total_mb': total_mb
                }
            }

        except Exception as e:
            return {
                'status': 'fail',
                'message': f'Storage check error: {str(e)}'
            }

    async def run_all_checks(self, db_path: str = "backend/data/vbs.db") -> Dict[str, Any]:
        """Run all health checks"""
        checks = {
            'database': await self.check_database_connection(db_path),
            'disk_space': await self.check_disk_space(),
            'memory': await self.check_memory_usage(),
            'circuit_breakers': await self.check_circuit_breakers(),
            'jobs': await self.check_job_health(),
            'storage': await self.check_storage_quotas()
        }

        # Determine overall status
        statuses = [check['status'] for check in checks.values()]
        if 'fail' in statuses:
            overall_status = 'unhealthy'
        elif 'warn' in statuses:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'

        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': self.monitor.get_uptime(),
            'checks': checks
        }


# Global health checker instance
health_checker = HealthChecker()


async def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health report"""
    return await health_checker.run_all_checks()


async def get_system_metrics() -> Dict[str, Any]:
    """Get detailed system metrics"""
    monitor = SystemMonitor()

    return {
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': monitor.get_uptime(),
        'memory': monitor.get_memory_usage(),
        'cpu': monitor.get_cpu_usage(),
        'disk': monitor.get_disk_usage(),
        'database': monitor.get_database_size("backend/data/vbs.db")
    }
