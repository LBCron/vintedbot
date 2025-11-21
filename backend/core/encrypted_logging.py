"""
Encrypted Logging System
Logs chiffrés pour protéger les données sensibles
"""
import json
import gzip
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from cryptography.fernet import Fernet
from loguru import logger
import os


class EncryptedLogger:
    """Logger with encryption for sensitive data"""

    def __init__(self, log_dir: str = "backend/data/logs_encrypted"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Get or create encryption key
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)

        # Current log file
        self.current_log_file = self.log_dir / f"log_{datetime.now().strftime('%Y%m%d')}.enc"

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = Path("backend/data/.log_encryption_key")
        key_file.parent.mkdir(parents=True, exist_ok=True)

        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Secure permissions (Unix)
            try:
                os.chmod(key_file, 0o600)
            except:
                pass
            return key

    def log(self, level: str, message: str, **kwargs):
        """
        Log encrypted message

        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            **kwargs: Additional data to log
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                "data": kwargs
            }

            # Convert to JSON
            log_json = json.dumps(log_entry, ensure_ascii=False)

            # Encrypt
            encrypted = self.cipher.encrypt(log_json.encode())

            # Append to file
            with open(self.current_log_file, 'ab') as f:
                f.write(encrypted + b'\n')

            # Also log to regular logger (without sensitive data)
            if kwargs:
                logger.log(level, f"{message} [encrypted_data]")
            else:
                logger.log(level, message)

        except Exception as e:
            logger.error(f"Failed to write encrypted log: {e}")

    def info(self, message: str, **kwargs):
        """Log INFO level"""
        self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log WARNING level"""
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log ERROR level"""
        self.log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log CRITICAL level"""
        self.log("CRITICAL", message, **kwargs)

    def metric(self, metric_name: str, value: Any, **tags):
        """
        Log metric

        Args:
            metric_name: Metric name
            value: Metric value
            **tags: Additional tags
        """
        self.log("METRIC", f"Metric: {metric_name}", value=value, **tags)

    def read_logs(self, date: str = None) -> list:
        """
        Read and decrypt logs

        Args:
            date: Date in YYYYMMDD format (default: today)

        Returns:
            List of log entries
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')

        log_file = self.log_dir / f"log_{date}.enc"

        if not log_file.exists():
            logger.warning(f"Log file not found for date: {date}")
            return []

        logs = []
        try:
            with open(log_file, 'rb') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            # Decrypt
                            decrypted = self.cipher.decrypt(line)
                            log_entry = json.loads(decrypted.decode())
                            logs.append(log_entry)
                        except Exception as e:
                            logger.error(f"Failed to decrypt log line: {e}")

            return logs

        except Exception as e:
            logger.error(f"Failed to read encrypted logs: {e}")
            return []

    def search_logs(self, query: str, start_date: str = None, end_date: str = None) -> list:
        """
        Search logs

        Args:
            query: Search query (matches message or level)
            start_date: Start date (YYYYMMDD)
            end_date: End date (YYYYMMDD)

        Returns:
            Matching log entries
        """
        if start_date is None:
            start_date = datetime.now().strftime('%Y%m%d')
        if end_date is None:
            end_date = start_date

        results = []

        # Get all log files in date range
        log_files = sorted(self.log_dir.glob("log_*.enc"))

        for log_file in log_files:
            date_str = log_file.stem.replace("log_", "")
            if start_date <= date_str <= end_date:
                logs = self.read_logs(date_str)
                for log in logs:
                    if query.lower() in log['message'].lower() or query.lower() in log['level'].lower():
                        results.append(log)

        return results

    def export_logs(self, output_file: str, start_date: str = None, end_date: str = None):
        """
        Export logs to JSON file (decrypted)

        Args:
            output_file: Output file path
            start_date: Start date (YYYYMMDD)
            end_date: End date (YYYYMMDD)
        """
        if start_date is None:
            start_date = datetime.now().strftime('%Y%m%d')
        if end_date is None:
            end_date = start_date

        all_logs = []

        # Collect logs
        log_files = sorted(self.log_dir.glob("log_*.enc"))
        for log_file in log_files:
            date_str = log_file.stem.replace("log_", "")
            if start_date <= date_str <= end_date:
                logs = self.read_logs(date_str)
                all_logs.extend(logs)

        # Export
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_logs, f, indent=2, ensure_ascii=False)

            logger.info(f"[OK] Exported {len(all_logs)} logs to {output_file}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to export logs: {e}")


# Global encrypted logger instance
encrypted_logger = EncryptedLogger()


if __name__ == "__main__":
    # Test encrypted logging
    logger_test = EncryptedLogger("backend/tests/test_logs")

    print("🔒 Testing Encrypted Logger\n")

    # Log some test data
    logger_test.info("Test info message", user="test_user", action="login")
    logger_test.warning("Test warning", ip="192.168.1.1")
    logger_test.error("Test error", error_code=500, details="Internal server error")
    logger_test.metric("requests_per_second", 150.5, endpoint="/api/vinted")

    print("[OK] Logs written (encrypted)\n")

    # Read logs
    print("📖 Reading encrypted logs:\n")
    logs = logger_test.read_logs()

    for log in logs:
        print(f"[{log['timestamp']}] {log['level']}: {log['message']}")
        if log.get('data'):
            print(f"   Data: {log['data']}")

    # Search
    print("\n[SEARCH] Searching for 'error':\n")
    results = logger_test.search_logs("error")
    print(f"Found {len(results)} results")

    print("\n[OK] Encrypted logging test complete!")
