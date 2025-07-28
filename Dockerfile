# Multi-stage build for JIRA Analytics
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r jira && useradd -r -g jira jira

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/jira/.local

# Copy application files
COPY --chown=jira:jira . .

# Create data directory for DuckDB
RUN mkdir -p /app/data && chown jira:jira /app/data

# Make CLI executable
RUN chmod +x jira_analytics_cli.py

# Switch to non-root user
USER jira

# Add local Python packages to PATH
ENV PATH=/home/jira/.local/bin:$PATH

# Set default database path
ENV JIRA_DB_PATH=/app/data/jira_data.duckdb

# Expose port for Marimo
EXPOSE 2718

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:2718/ || exit 1

# Default command
CMD ["python", "jira_analytics_cli.py", "--host", "0.0.0.0", "--port", "2718"]