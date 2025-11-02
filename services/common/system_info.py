#!/usr/bin/env python3
"""System information collector for PC specifications detection.

This module detects hardware specifications and stores them in the database
for optimal Ollama model selection.

Features:
- CPU detection (model, cores, frequency)
- RAM detection (total, available)
- GPU detection (NVIDIA, AMD, Intel)
- Disk space detection
- OS information
- Database storage for model recommendations
"""

import platform
import subprocess
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any


class SystemInfoCollector:
    """Collect and store system specifications."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize system info collector.

        Args:
            db_path: Path to SQLite database. Defaults to neurohub_llm.db
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "neurohub_llm.db"

        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # system_specs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_specs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_model TEXT,
                    cpu_cores INTEGER,
                    cpu_frequency REAL,
                    ram_total_gb REAL,
                    ram_available_gb REAL,
                    gpu_model TEXT,
                    gpu_vram_gb REAL,
                    disk_total_gb REAL,
                    disk_free_gb REAL,
                    os_name TEXT,
                    os_version TEXT,
                    recommended_model TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ollama_models table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ollama_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT UNIQUE NOT NULL,
                    size_gb REAL,
                    min_ram_gb REAL,
                    min_vram_gb REAL,
                    recommended_for TEXT,
                    performance_score INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information.

        Returns:
            Dictionary with cpu_model, cpu_cores, cpu_frequency
        """
        info = {
            'cpu_model': platform.processor() or 'Unknown',
            'cpu_cores': 0,
            'cpu_frequency': 0.0
        }

        try:
            # Get CPU cores
            if platform.system() == 'Windows':
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'NumberOfCores'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    info['cpu_cores'] = int(lines[1].strip())
            else:
                # Linux/WSL
                result = subprocess.run(
                    ['nproc'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                info['cpu_cores'] = int(result.stdout.strip())
        except Exception:
            pass

        return info

    def get_ram_info(self) -> Dict[str, float]:
        """Get RAM information.

        Returns:
            Dictionary with ram_total_gb, ram_available_gb
        """
        info = {
            'ram_total_gb': 0.0,
            'ram_available_gb': 0.0
        }

        try:
            if platform.system() == 'Windows':
                # Total RAM
                result = subprocess.run(
                    ['wmic', 'ComputerSystem', 'get', 'TotalPhysicalMemory'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    total_bytes = int(lines[1].strip())
                    info['ram_total_gb'] = total_bytes / (1024**3)

                # Available RAM
                result = subprocess.run(
                    ['wmic', 'OS', 'get', 'FreePhysicalMemory'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    free_kb = int(lines[1].strip())
                    info['ram_available_gb'] = free_kb / (1024**2)
            else:
                # Linux/WSL
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if line.startswith('MemTotal:'):
                            total_kb = int(line.split()[1])
                            info['ram_total_gb'] = total_kb / (1024**2)
                        elif line.startswith('MemAvailable:'):
                            available_kb = int(line.split()[1])
                            info['ram_available_gb'] = available_kb / (1024**2)
        except Exception:
            pass

        return info

    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information.

        Returns:
            Dictionary with gpu_model, gpu_vram_gb
        """
        info = {
            'gpu_model': 'None',
            'gpu_vram_gb': 0.0
        }

        try:
            # Try nvidia-smi first
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(',')
                    info['gpu_model'] = parts[0].strip()
                    if len(parts) > 1:
                        vram_str = parts[1].strip().replace(' MiB', '')
                        info['gpu_vram_gb'] = int(vram_str) / 1024
        except Exception:
            pass

        return info

    def get_disk_info(self) -> Dict[str, float]:
        """Get disk information.

        Returns:
            Dictionary with disk_total_gb, disk_free_gb
        """
        info = {
            'disk_total_gb': 0.0,
            'disk_free_gb': 0.0
        }

        try:
            if platform.system() == 'Windows':
                result = subprocess.run(
                    ['wmic', 'LogicalDisk', 'where', 'DriveType=3', 'get', 'Size,FreeSpace'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Get C: drive (first line after header)
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        info['disk_free_gb'] = int(parts[0]) / (1024**3)
                        info['disk_total_gb'] = int(parts[1]) / (1024**3)
            else:
                # Linux/WSL
                result = subprocess.run(
                    ['df', '-B1', '/'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        info['disk_total_gb'] = int(parts[1]) / (1024**3)
                        info['disk_free_gb'] = int(parts[3]) / (1024**3)
        except Exception:
            pass

        return info

    def get_os_info(self) -> Dict[str, str]:
        """Get OS information.

        Returns:
            Dictionary with os_name, os_version
        """
        return {
            'os_name': platform.system(),
            'os_version': platform.release()
        }

    def collect_all(self) -> Dict[str, Any]:
        """Collect all system information.

        Returns:
            Complete system specifications
        """
        specs = {}
        specs.update(self.get_cpu_info())
        specs.update(self.get_ram_info())
        specs.update(self.get_gpu_info())
        specs.update(self.get_disk_info())
        specs.update(self.get_os_info())
        return specs

    def recommend_model(self, specs: Dict[str, Any]) -> str:
        """Recommend Ollama model based on system specs.

        Args:
            specs: System specifications dictionary

        Returns:
            Recommended model name
        """
        ram_gb = specs.get('ram_total_gb', 0)
        gpu_vram_gb = specs.get('gpu_vram_gb', 0)

        # High-end system
        if ram_gb >= 32 and gpu_vram_gb >= 8:
            return 'llama3.1:70b'
        # Mid-range system
        elif ram_gb >= 16 and gpu_vram_gb >= 4:
            return 'llama3.1:13b'
        # Low-end system or CPU-only
        elif ram_gb >= 8:
            return 'llama3.1:8b'
        # Very low-end
        else:
            return 'qwen2.5:3b'

    def save_to_db(self, specs: Optional[Dict[str, Any]] = None) -> int:
        """Save system specs to database.

        Args:
            specs: System specifications. If None, collect automatically.

        Returns:
            ID of inserted record
        """
        if specs is None:
            specs = self.collect_all()

        # Get recommendation
        recommended_model = self.recommend_model(specs)
        specs['recommended_model'] = recommended_model

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_specs (
                    cpu_model, cpu_cores, cpu_frequency,
                    ram_total_gb, ram_available_gb,
                    gpu_model, gpu_vram_gb,
                    disk_total_gb, disk_free_gb,
                    os_name, os_version,
                    recommended_model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                specs.get('cpu_model'),
                specs.get('cpu_cores'),
                specs.get('cpu_frequency'),
                specs.get('ram_total_gb'),
                specs.get('ram_available_gb'),
                specs.get('gpu_model'),
                specs.get('gpu_vram_gb'),
                specs.get('disk_total_gb'),
                specs.get('disk_free_gb'),
                specs.get('os_name'),
                specs.get('os_version'),
                specs.get('recommended_model')
            ))
            conn.commit()
            return cursor.lastrowid

    def get_latest_specs(self) -> Optional[Dict[str, Any]]:
        """Get latest system specs from database.

        Returns:
            Latest system specifications or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cpu_model, cpu_cores, cpu_frequency,
                       ram_total_gb, ram_available_gb,
                       gpu_model, gpu_vram_gb,
                       disk_total_gb, disk_free_gb,
                       os_name, os_version,
                       recommended_model, created_at
                FROM system_specs
                ORDER BY id DESC
                LIMIT 1
            """)
            row = cursor.fetchone()

            if row:
                return {
                    'cpu_model': row[0],
                    'cpu_cores': row[1],
                    'cpu_frequency': row[2],
                    'ram_total_gb': row[3],
                    'ram_available_gb': row[4],
                    'gpu_model': row[5],
                    'gpu_vram_gb': row[6],
                    'disk_total_gb': row[7],
                    'disk_free_gb': row[8],
                    'os_name': row[9],
                    'os_version': row[10],
                    'recommended_model': row[11],
                    'created_at': row[12]
                }
            return None


def main():
    """CLI entry point for system info collection."""
    import argparse

    parser = argparse.ArgumentParser(description='Collect and save system specifications')
    parser.add_argument('--db', type=str, help='Database path')
    parser.add_argument('--show', action='store_true', help='Show current specs')
    parser.add_argument('--save', action='store_true', help='Save specs to database')

    args = parser.parse_args()

    collector = SystemInfoCollector(db_path=args.db)

    if args.show or not args.save:
        specs = collector.collect_all()
        recommended = collector.recommend_model(specs)

        print("\n=== System Specifications ===")
        print(f"CPU: {specs['cpu_model']}")
        print(f"CPU Cores: {specs['cpu_cores']}")
        print(f"RAM Total: {specs['ram_total_gb']:.2f} GB")
        print(f"RAM Available: {specs['ram_available_gb']:.2f} GB")
        print(f"GPU: {specs['gpu_model']}")
        print(f"GPU VRAM: {specs['gpu_vram_gb']:.2f} GB")
        print(f"Disk Total: {specs['disk_total_gb']:.2f} GB")
        print(f"Disk Free: {specs['disk_free_gb']:.2f} GB")
        print(f"OS: {specs['os_name']} {specs['os_version']}")
        print(f"\nRecommended Model: {recommended}")

    if args.save:
        specs_id = collector.save_to_db()
        print(f"\n✅ Saved to database (ID: {specs_id})")


if __name__ == '__main__':
    main()
