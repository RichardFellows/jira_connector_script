#!/usr/bin/env python3
"""
JIRA Server Data Extractor

Extracts issue data from JIRA Server v9.12 using REST API v2
and stores it in a local DuckDB database for analysis.

Features:
- Project selection
- Date range filtering
- Incremental updates
- Customizable field selection
- Custom field mapping
"""

import os
import sys
import json
import requests
import duckdb
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
# from urllib.parse import urljoin  # unused
import logging


class JIRAExtractor:
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_path: str = "jira_data.duckdb",
    ):
        self.base_url = base_url.rstrip("/")
        self.db_path = db_path
        self.session = requests.Session()

        # Configure authentication
        if token:
            # Use PAT (Personal Access Token)
            self.session.headers.update(
                {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            )
            self.auth_method = "PAT"
        elif username and password:
            # Use basic auth
            self.session.auth = (username, password)
            self.session.headers.update({"Content-Type": "application/json"})
            self.auth_method = "Basic"
        else:
            raise ValueError("Either token or username/password must be provided")

        # Initialize database
        self.init_database()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def init_database(self):
        """Initialize DuckDB database with required tables"""
        conn = duckdb.connect(self.db_path)

        # Create issues table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS issues (
                id VARCHAR PRIMARY KEY,
                key VARCHAR UNIQUE,
                project_key VARCHAR,
                project_name VARCHAR,
                issue_type VARCHAR,
                status VARCHAR,
                priority VARCHAR,
                summary VARCHAR,
                description TEXT,
                assignee VARCHAR,
                reporter VARCHAR,
                created TIMESTAMP,
                updated TIMESTAMP,
                resolved TIMESTAMP,
                due_date TIMESTAMP,
                labels VARCHAR[],
                components VARCHAR[],
                fix_versions VARCHAR[],
                affects_versions VARCHAR[],
                custom_fields JSON,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create extraction log table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS extraction_log (
                id INTEGER PRIMARY KEY,
                project_key VARCHAR,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                issues_extracted INTEGER,
                extraction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.close()

    def test_connection(self) -> bool:
        """Test connection to JIRA server"""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/2/serverInfo")
            response.raise_for_status()
            server_info = response.json()
            self.logger.info(
                f"Connected to JIRA Server {server_info.get('version', 'Unknown')} using {self.auth_method} authentication"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to JIRA: {e}")
            return False

    def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of available projects"""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/2/project")
            response.raise_for_status()
            projects = response.json()
            return [{"key": p["key"], "name": p["name"]} for p in projects]
        except Exception as e:
            self.logger.error(f"Failed to get projects: {e}")
            return []

    def get_custom_fields(self) -> Dict[str, str]:
        """Get mapping of custom field IDs to names"""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/2/field")
            response.raise_for_status()
            fields = response.json()

            custom_fields = {}
            for field in fields:
                if field["custom"]:
                    custom_fields[field["id"]] = field["name"]

            return custom_fields
        except Exception as e:
            self.logger.error(f"Failed to get custom fields: {e}")
            return {}

    def extract_issues(
        self,
        project_key: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fields: Optional[List[str]] = None,
        custom_field_mapping: Optional[Dict[str, str]] = None,
        incremental: bool = False,
    ) -> int:
        """Extract issues from JIRA project"""

        # Build JQL query
        jql_parts = [f"project = {project_key}"]

        if incremental:
            # Get last extraction date for this project
            conn = duckdb.connect(self.db_path)
            result = conn.execute(
                """
                SELECT MAX(extraction_time) as last_extraction
                FROM extraction_log
                WHERE project_key = ?
            """,
                [project_key],
            ).fetchone()
            conn.close()

            if result and result[0]:
                last_extraction = result[0]
                jql_parts.append(
                    f"updated >= '{last_extraction.strftime('%Y-%m-%d %H:%M')}'"
                )

        if start_date:
            jql_parts.append(f"created >= '{start_date}'")
        if end_date:
            jql_parts.append(f"created <= '{end_date}'")

        jql = " AND ".join(jql_parts)

        # Default fields to extract
        default_fields = [
            "key",
            "summary",
            "description",
            "issuetype",
            "status",
            "priority",
            "assignee",
            "reporter",
            "created",
            "updated",
            "resolutiondate",
            "duedate",
            "labels",
            "components",
            "fixVersions",
            "versions",
        ]

        if fields:
            extract_fields = fields
        else:
            extract_fields = default_fields

        # Add custom fields if specified
        if custom_field_mapping:
            extract_fields.extend(custom_field_mapping.keys())

        issues_extracted = 0
        start_at = 0
        max_results = 100

        conn = duckdb.connect(self.db_path)

        try:
            while True:
                # Make API request
                params = {
                    "jql": jql,
                    "startAt": str(start_at),
                    "maxResults": str(max_results),
                    "fields": ",".join(extract_fields),
                    "expand": "changelog",
                }

                response = self.session.get(
                    f"{self.base_url}/rest/api/2/search", params=params
                )
                response.raise_for_status()
                data = response.json()

                issues = data.get("issues", [])
                if not issues:
                    break

                # Process and insert issues
                for issue in issues:
                    self.insert_issue(conn, issue, custom_field_mapping)
                    issues_extracted += 1

                self.logger.info(f"Extracted {issues_extracted} issues so far...")

                # Check if we've got all issues
                if start_at + max_results >= data["total"]:
                    break

                start_at += max_results

            # Log extraction
            conn.execute(
                """
                INSERT INTO extraction_log (project_key, start_date, end_date, issues_extracted)
                VALUES (?, ?, ?, ?)
            """,
                [project_key, start_date, end_date, issues_extracted],
            )

        except Exception as e:
            self.logger.error(f"Failed to extract issues: {e}")
            raise
        finally:
            conn.close()

        return issues_extracted

    def insert_issue(
        self,
        conn: duckdb.DuckDBPyConnection,
        issue: Dict[str, Any],
        custom_field_mapping: Optional[Dict[str, str]] = None,
    ):
        """Insert or update issue in database"""
        fields = issue["fields"]

        # Extract standard fields
        issue_data = {
            "id": issue["id"],
            "key": issue["key"],
            "project_key": fields.get("project", {}).get("key"),
            "project_name": fields.get("project", {}).get("name"),
            "issue_type": fields.get("issuetype", {}).get("name"),
            "status": fields.get("status", {}).get("name"),
            "priority": (
                fields.get("priority", {}).get("name")
                if fields.get("priority")
                else None
            ),
            "summary": fields.get("summary"),
            "description": fields.get("description"),
            "assignee": (
                fields.get("assignee", {}).get("displayName")
                if fields.get("assignee")
                else None
            ),
            "reporter": (
                fields.get("reporter", {}).get("displayName")
                if fields.get("reporter")
                else None
            ),
            "created": self.parse_jira_datetime(fields.get("created")),
            "updated": self.parse_jira_datetime(fields.get("updated")),
            "resolved": self.parse_jira_datetime(fields.get("resolutiondate")),
            "due_date": self.parse_jira_datetime(fields.get("duedate")),
            "labels": [label for label in fields.get("labels", [])],
            "components": [comp["name"] for comp in fields.get("components", [])],
            "fix_versions": [ver["name"] for ver in fields.get("fixVersions", [])],
            "affects_versions": [ver["name"] for ver in fields.get("versions", [])],
        }

        # Extract custom fields
        custom_fields = {}
        if custom_field_mapping:
            for field_id, display_name in custom_field_mapping.items():
                if field_id in fields:
                    custom_fields[display_name] = fields[field_id]

        issue_data["custom_fields"] = (
            json.dumps(custom_fields) if custom_fields else None
        )

        # Insert or replace issue
        conn.execute(
            """
            INSERT OR REPLACE INTO issues (
                id, key, project_key, project_name, issue_type, status, priority,
                summary, description, assignee, reporter, created, updated, resolved,
                due_date, labels, components, fix_versions, affects_versions, custom_fields
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                issue_data["id"],
                issue_data["key"],
                issue_data["project_key"],
                issue_data["project_name"],
                issue_data["issue_type"],
                issue_data["status"],
                issue_data["priority"],
                issue_data["summary"],
                issue_data["description"],
                issue_data["assignee"],
                issue_data["reporter"],
                issue_data["created"],
                issue_data["updated"],
                issue_data["resolved"],
                issue_data["due_date"],
                issue_data["labels"],
                issue_data["components"],
                issue_data["fix_versions"],
                issue_data["affects_versions"],
                issue_data["custom_fields"],
            ],
        )

    def parse_jira_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse JIRA datetime string to Python datetime"""
        if not datetime_str:
            return None

        try:
            # JIRA typically returns ISO format with timezone
            return datetime.fromisoformat(
                datetime_str.replace("Z", "+00:00").replace(".000", "")
            )
        except Exception:
            return None


def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    """Load configuration from file"""
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    return {}


def save_config(config: Dict[str, Any], config_file: str = "config.json"):
    """Save configuration to file"""
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Extract JIRA issues to DuckDB")
    parser.add_argument("--url", required=True, help="JIRA Server base URL")
    parser.add_argument("--token", help="JIRA Personal Access Token")
    parser.add_argument("--username", help="JIRA username (for basic auth)")
    parser.add_argument("--password", help="JIRA password (for basic auth)")
    parser.add_argument("--project", help="Project key to extract")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--incremental", action="store_true", help="Incremental update")
    parser.add_argument(
        "--db-path", default="jira_data.duckdb", help="DuckDB file path"
    )
    parser.add_argument("--config", default="config.json", help="Configuration file")
    parser.add_argument(
        "--list-projects", action="store_true", help="List available projects"
    )
    parser.add_argument("--list-fields", action="store_true", help="List custom fields")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Validate authentication arguments
    if not args.token and not (args.username and args.password):
        print(
            "Error: Either --token or both --username and --password must be provided"
        )
        sys.exit(1)

    # Initialize extractor
    extractor = JIRAExtractor(
        base_url=args.url,
        token=args.token,
        username=args.username,
        password=args.password,
        db_path=args.db_path,
    )

    # Test connection
    if not extractor.test_connection():
        sys.exit(1)

    # List projects if requested
    if args.list_projects:
        projects = extractor.get_projects()
        print("\nAvailable projects:")
        for project in projects:
            print(f"  {project['key']}: {project['name']}")
        return

    # List custom fields if requested
    if args.list_fields:
        fields = extractor.get_custom_fields()
        print("\nCustom fields:")
        for field_id, field_name in fields.items():
            print(f"  {field_id}: {field_name}")
        return

    # Extract issues
    if not args.project:
        print("Please specify a project key using --project")
        sys.exit(1)

    # Get custom field mapping from config
    custom_field_mapping = config.get("custom_field_mapping", {})
    fields = config.get("fields")

    try:
        count = extractor.extract_issues(
            project_key=args.project,
            start_date=args.start_date,
            end_date=args.end_date,
            fields=fields,
            custom_field_mapping=custom_field_mapping,
            incremental=args.incremental,
        )
        print(f"Successfully extracted {count} issues from project {args.project}")
    except Exception as e:
        print(f"Error extracting issues: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
