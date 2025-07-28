# JIRA Server Data Extractor

A Python script to extract issue data from JIRA Server v9.12 using REST API v2 and store it in a local DuckDB database for analysis.

## Features

- **Project Selection**: Choose which JIRA project to extract data from
- **Date Range Filtering**: Extract issues created within specific date ranges
- **Incremental Updates**: Only fetch issues updated since the last extraction
- **Customizable Fields**: Configure which fields to extract
- **Custom Field Mapping**: Map custom field IDs to readable display names
- **Local Storage**: Data stored in efficient DuckDB database format

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Copy the example configuration file:
```bash
cp config.json.example config.json
```

3. Edit `config.json` to configure your custom fields and field selection.

## Usage

### Basic Usage

#### Using Personal Access Token (Recommended)

Extract all issues from a project:
```bash
python jira_extractor.py --url https://your-jira-server.com --token your_personal_access_token --project PROJ
```

#### Using Username/Password

Extract all issues from a project:
```bash
python jira_extractor.py --url https://your-jira-server.com --username your_username --password your_password --project PROJ
```

### List Available Projects

```bash
# With PAT
python jira_extractor.py --url https://your-jira-server.com --token your_token --list-projects

# With username/password
python jira_extractor.py --url https://your-jira-server.com --username your_username --password your_password --list-projects
```

### List Custom Fields

```bash
# With PAT
python jira_extractor.py --url https://your-jira-server.com --token your_token --list-fields

# With username/password
python jira_extractor.py --url https://your-jira-server.com --username your_username --password your_password --list-fields
```

### Extract with Date Range

```bash
# With PAT
python jira_extractor.py --url https://your-jira-server.com --token your_token --project PROJ --start-date 2024-01-01 --end-date 2024-12-31

# With username/password
python jira_extractor.py --url https://your-jira-server.com --username your_username --password your_password --project PROJ --start-date 2024-01-01 --end-date 2024-12-31
```

### Incremental Update

```bash
# With PAT
python jira_extractor.py --url https://your-jira-server.com --token your_token --project PROJ --incremental

# With username/password
python jira_extractor.py --url https://your-jira-server.com --username your_username --password your_password --project PROJ --incremental
```

### Custom Database Path

```bash
# With PAT
python jira_extractor.py --url https://your-jira-server.com --token your_token --project PROJ --db-path /path/to/custom.duckdb

# With username/password
python jira_extractor.py --url https://your-jira-server.com --username your_username --password your_password --project PROJ --db-path /path/to/custom.duckdb
```

## Configuration

Edit `config.json` to customize:

### Custom Field Mapping

Map JIRA custom field IDs to readable names:
```json
{
  "custom_field_mapping": {
    "customfield_10001": "Story Points",
    "customfield_10002": "Epic Link",
    "customfield_10003": "Sprint"
  }
}
```

### Field Selection

Specify which fields to extract:
```json
{
  "fields": [
    "key",
    "summary",
    "description",
    "issuetype",
    "status",
    "priority",
    "customfield_10001"
  ]
}
```

## Database Schema

The script creates two tables in DuckDB:

### issues table
- `id`: JIRA issue ID
- `key`: JIRA issue key (e.g., PROJ-123)
- `project_key`: Project key
- `project_name`: Project name
- `issue_type`: Issue type (Bug, Story, etc.)
- `status`: Current status
- `priority`: Priority level
- `summary`: Issue summary
- `description`: Issue description
- `assignee`: Assigned user
- `reporter`: Reporter user
- `created`: Creation timestamp
- `updated`: Last update timestamp
- `resolved`: Resolution timestamp
- `due_date`: Due date
- `labels`: Array of labels
- `components`: Array of components
- `fix_versions`: Array of fix versions
- `affects_versions`: Array of affected versions
- `custom_fields`: JSON object with custom field data
- `extracted_at`: Extraction timestamp

### extraction_log table
- `id`: Log entry ID
- `project_key`: Project that was extracted
- `start_date`: Start date filter used
- `end_date`: End date filter used
- `issues_extracted`: Number of issues extracted
- `extraction_time`: When extraction was performed

## Querying Data

Use DuckDB CLI or any SQL tool to query the data:

```sql
-- Connect to database
.open jira_data.duckdb

-- Count issues by status
SELECT status, COUNT(*) as count 
FROM issues 
GROUP BY status 
ORDER BY count DESC;

-- Issues created in the last 30 days
SELECT key, summary, created 
FROM issues 
WHERE created >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY created DESC;

-- Custom field analysis
SELECT 
    key, 
    summary,
    JSON_EXTRACT(custom_fields, '$.Story Points') as story_points
FROM issues 
WHERE custom_fields IS NOT NULL;
```

## Authentication

### Personal Access Token (Recommended)

Personal Access Tokens are more secure than username/password authentication:

1. Generate a PAT in JIRA: Profile → Personal Access Tokens → Create token
2. Use the `--token` parameter instead of `--username` and `--password`
3. PATs can be revoked without changing your password
4. PATs have configurable expiration dates

### Username/Password (Legacy)

Basic authentication is still supported but less secure:
- Ensure your JIRA server allows basic authentication
- Consider using application passwords instead of your main password

## Security Notes

- **Use Personal Access Tokens when possible** - more secure than passwords
- Store credentials securely (consider using environment variables)
- Use HTTPS for JIRA server connections
- Database files contain sensitive project data - protect accordingly
- Regularly rotate tokens and passwords

## 🚀 Quick Deployment

### Docker (Recommended)
```bash
# Quick start with Docker Compose
git clone <repository-url>
cd jira_connector_script
make deploy

# Access dashboard at http://localhost:2718
```

### Python Package
```bash
# Install and run locally
pip install -e .
jira-analytics
```

### Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start analytics dashboard
python jira_analytics_cli.py
```

## 📦 Distribution & Deployment

This project is packaged for easy distribution and deployment:

- **Python Package**: Install via pip with CLI commands
- **Docker Container**: Containerized deployment with Docker/Compose  
- **Production Ready**: Includes reverse proxy, SSL, monitoring configs
- **CI/CD Pipeline**: Automated testing, building, and deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment options including:
- Local development setup
- Team server deployment  
- Production Docker deployment
- Security configurations
- Monitoring and maintenance

## 🔧 Development Commands

```bash
make help          # Show all available commands
make setup         # Quick setup for new users
make analytics     # Start dashboard
make deploy        # Docker Compose deployment
make docker        # Build Docker image
make test          # Run tests and validation
make backup        # Backup database
```

## Troubleshooting

- Ensure JIRA REST API v2 is enabled on your server
- Check network connectivity to JIRA server
- Verify credentials have necessary project permissions
- For large projects, extraction may take time - monitor logs for progress
- See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting guide