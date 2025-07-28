#!/usr/bin/env python3
"""
CLI wrapper for JIRA Analytics Marimo notebook
"""

import sys
import subprocess
import argparse
import os


def main():
    """Main CLI entry point for JIRA Analytics"""
    parser = argparse.ArgumentParser(
        description="JIRA Analytics Dashboard - Interactive data analysis for agile teams"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=2718,
        help="Port to run the Marimo server on (default: 2718)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind the server to (default: localhost)",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no browser auto-open)",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="jira_data.duckdb",
        help="Path to DuckDB database file (default: jira_data.duckdb)",
    )

    args = parser.parse_args()

    # Find the analytics notebook
    script_dir = os.path.dirname(os.path.abspath(__file__))
    notebook_path = os.path.join(script_dir, "jira_analytics.py")

    if not os.path.exists(notebook_path):
        print(f"Error: Analytics notebook not found at {notebook_path}")
        sys.exit(1)

    # Build marimo command
    cmd = ["marimo", "run", notebook_path]
    cmd.extend(["--port", str(args.port)])
    cmd.extend(["--host", args.host])

    if args.headless:
        cmd.append("--headless")

    # Set environment variable for database path
    env = os.environ.copy()
    env["JIRA_DB_PATH"] = args.db_path

    print("🚀 Starting JIRA Analytics Dashboard...")
    print(f"📊 Dashboard will be available at http://{args.host}:{args.port}")
    print(f"💾 Using database: {args.db_path}")
    print(f"🔄 Command: {' '.join(cmd)}")
    print()

    try:
        # Run the marimo server
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting analytics dashboard: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Analytics dashboard stopped by user")
        sys.exit(0)
    except FileNotFoundError:
        print("❌ Error: 'marimo' command not found. Please install marimo:")
        print("   pip install marimo>=0.8.0")
        sys.exit(1)


if __name__ == "__main__":
    main()
