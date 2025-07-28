import marimo

__generated_with = "0.8.0"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import duckdb
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import json
    import subprocess
    import sys
    import os
    from datetime import datetime, timedelta

    return (
        datetime,
        duckdb,
        go,
        json,
        make_subplots,
        mo,
        os,
        pd,
        px,
        subprocess,
        sys,
        timedelta,
    )


@app.cell
def __():
    mo.md(
        r"""
        # JIRA Analytics Dashboard
        
        **For ScrumMasters and Product Owners**
        
        This dashboard provides insights into estimation accuracy and team velocity using data extracted from JIRA.
        You can also refresh data directly from JIRA using the controls below.
        """
    )
    return


@app.cell
def __():
    mo.md("## 🔄 Data Refresh Configuration")
    return


@app.cell
def __():
    # JIRA connection settings
    jira_url = mo.ui.text(
        label="JIRA Server URL:",
        placeholder="https://your-jira-server.com",
        full_width=True,
    )

    auth_method = mo.ui.radio(
        options=["token", "username_password"],
        value="token",
        label="Authentication method:",
    )

    mo.vstack([jira_url, auth_method])
    return auth_method, jira_url


@app.cell
def __(auth_method, mo):
    # Authentication inputs based on selected method
    if auth_method.value == "token":
        token_input = mo.ui.text(
            label="Personal Access Token:",
            kind="password",
            placeholder="Enter your JIRA PAT",
        )
        username_input = None
        password_input = None
        auth_inputs = token_input
    else:
        token_input = None
        username_input = mo.ui.text(
            label="Username:", placeholder="Enter your JIRA username"
        )
        password_input = mo.ui.text(
            label="Password:", kind="password", placeholder="Enter your JIRA password"
        )
        auth_inputs = mo.vstack([username_input, password_input])

    auth_inputs
    return auth_inputs, password_input, token_input, username_input


@app.cell
def __():
    # Data refresh settings
    refresh_project = mo.ui.text(
        label="Project Key for Refresh:", placeholder="e.g., PROJ1", full_width=True
    )

    refresh_date_range = mo.ui.date_range(
        label="Date range for issues to refresh:",
        start=datetime.now().date() - timedelta(days=30),
        stop=datetime.now().date(),
    )

    incremental_update = mo.ui.checkbox(
        label="Incremental update (only fetch changed issues)", value=True
    )

    mo.vstack([refresh_project, refresh_date_range, incremental_update])
    return incremental_update, refresh_date_range, refresh_project


@app.cell
def __(
    auth_method,
    datetime,
    incremental_update,
    jira_url,
    mo,
    password_input,
    refresh_date_range,
    refresh_project,
    subprocess,
    sys,
    token_input,
    username_input,
):
    # Data refresh trigger
    refresh_button = mo.ui.button(
        label="🔄 Refresh JIRA Data",
        kind="success",
        disabled=not (
            jira_url.value
            and refresh_project.value
            and (
                token_input.value
                if auth_method.value == "token"
                else (
                    username_input
                    and password_input
                    and username_input.value
                    and password_input.value
                )
            )
        ),
    )

    # State to track refresh status
    refresh_status = mo.ui.text(value="", disabled=True)

    if refresh_button.value:
        try:
            # Build command arguments
            cmd = [sys.executable, "jira_extractor.py"]

            # Add URL
            cmd.extend(["--url", jira_url.value])

            # Add authentication
            if auth_method.value == "token":
                cmd.extend(["--token", token_input.value])
            else:
                cmd.extend(
                    [
                        "--username",
                        username_input.value,
                        "--password",
                        password_input.value,
                    ]
                )

            # Add project
            cmd.extend(["--project", refresh_project.value])

            # Add date range if specified
            if refresh_date_range.value:
                start_date, end_date = refresh_date_range.value
                cmd.extend(
                    [
                        "--start-date",
                        start_date.strftime("%Y-%m-%d"),
                        "--end-date",
                        end_date.strftime("%Y-%m-%d"),
                    ]
                )

            # Add incremental flag
            if incremental_update.value:
                cmd.append("--incremental")

            # Execute the command
            refresh_status._update("🔄 Refreshing data from JIRA...")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                refresh_status._update(
                    f"✅ Data refresh completed successfully! {datetime.now().strftime('%H:%M:%S')}"
                )
            else:
                refresh_status._update(f"❌ Refresh failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            refresh_status._update("⏱️ Refresh timed out after 5 minutes")
        except Exception as e:
            refresh_status._update(f"❌ Error during refresh: {str(e)}")

    mo.vstack([refresh_button, refresh_status if refresh_status.value else mo.md("")])
    return cmd, refresh_button, refresh_status, result


@app.cell
def __():
    mo.md("---")
    return


@app.cell
def __():
    # Database connection and configuration
    db_path = mo.ui.text(
        label="DuckDB file path:",
        value="jira_data.duckdb",
        placeholder="Enter path to your JIRA DuckDB file",
    )

    project_filter = mo.ui.text(
        label="Project filter (optional):",
        placeholder="e.g., PROJ1,PROJ2 or leave empty for all",
    )

    mo.md(
        f"""
    ## Configuration
    
    {db_path}
    {project_filter}
    """
    )
    return db_path, project_filter


@app.cell
def __(db_path, duckdb, json, pd, refresh_status):
    # Load data from DuckDB (auto-reload when refresh completes)
    reload_trigger = refresh_status.value if "✅" in refresh_status.value else ""

    try:
        conn = duckdb.connect(db_path.value)

        # Load issues data
        issues_query = """
        SELECT
            id, key, project_key, project_name, issue_type, status, priority,
            summary, assignee, reporter, created, updated, resolved, due_date,
            labels, components, fix_versions, affects_versions, custom_fields,
            extracted_at
        FROM issues
        WHERE 1=1
        """

        issues_df = conn.execute(issues_query).df()

        # Load extraction log
        log_df = conn.execute(
            "SELECT * FROM extraction_log ORDER BY extraction_time DESC"
        ).df()

        conn.close()

        # Parse custom fields JSON
        if not issues_df.empty and "custom_fields" in issues_df.columns:
            issues_df["story_points"] = issues_df["custom_fields"].apply(
                lambda x: (
                    json.loads(x).get("Story Points") if x and x != "null" else None
                )
            )
            issues_df["epic_link"] = issues_df["custom_fields"].apply(
                lambda x: json.loads(x).get("Epic Link") if x and x != "null" else None
            )
            issues_df["sprint"] = issues_df["custom_fields"].apply(
                lambda x: json.loads(x).get("Sprint") if x and x != "null" else None
            )

        # Convert date columns
        date_cols = ["created", "updated", "resolved", "due_date", "extracted_at"]
        for col in date_cols:
            if col in issues_df.columns:
                issues_df[col] = pd.to_datetime(issues_df[col], errors="coerce")

        data_loaded = True

        # Show last refresh time if available
        last_refresh = ""
        if not log_df.empty and "extraction_time" in log_df.columns:
            last_extraction = pd.to_datetime(log_df.iloc[0]["extraction_time"])
            last_refresh = (
                f" (Last updated: {last_extraction.strftime('%Y-%m-%d %H:%M:%S')})"
            )

        load_message = f"✅ Loaded {len(issues_df)} issues from {len(issues_df['project_key'].unique())} projects{last_refresh}"

    except Exception as e:
        data_loaded = False
        load_message = f"❌ Error loading data: {str(e)}"
        issues_df = pd.DataFrame()
        log_df = pd.DataFrame()

    load_message
    return (
        conn,
        data_loaded,
        date_cols,
        issues_df,
        issues_query,
        last_refresh,
        load_message,
        log_df,
        reload_trigger,
    )


@app.cell
def __(data_loaded, issues_df, mo, project_filter):
    if not data_loaded or issues_df.empty:
        mo.stop(True, "No data available. Please check your database path.")

    # Apply project filter if specified
    filtered_df = issues_df.copy()
    if project_filter.value.strip():
        projects = [p.strip() for p in project_filter.value.split(",")]
        filtered_df = filtered_df[filtered_df["project_key"].isin(projects)]

    mo.md(
        f"""
    ## Data Overview
    
    **Filtered Dataset:** {len(filtered_df)} issues across {len(filtered_df['project_key'].unique())} projects
    
    **Projects:** {', '.join(filtered_df['project_key'].unique())}
    """
    )
    return filtered_df, projects


@app.cell
def __(filtered_df, mo):
    # Interactive filters
    date_range = mo.ui.date_range(
        start=filtered_df["created"].min().date() if not filtered_df.empty else None,
        stop=filtered_df["created"].max().date() if not filtered_df.empty else None,
        label="Date range for analysis:",
    )

    issue_types = mo.ui.multiselect(
        options=(
            list(filtered_df["issue_type"].unique()) if not filtered_df.empty else []
        ),
        label="Issue types to include:",
        value=list(filtered_df["issue_type"].unique()) if not filtered_df.empty else [],
    )

    statuses = mo.ui.multiselect(
        options=list(filtered_df["status"].unique()) if not filtered_df.empty else [],
        label="Statuses to include:",
        value=list(filtered_df["status"].unique()) if not filtered_df.empty else [],
    )

    mo.md(
        f"""
    ## Filters
    
    {date_range}
    {issue_types}
    {statuses}
    """
    )
    return date_range, issue_types, statuses


@app.cell
def __(date_range, filtered_df, issue_types, statuses):
    # Apply filters to create analysis dataset
    filtered_analysis_df = filtered_df.copy()

    if date_range.value:
        start_date, end_date = date_range.value
        filtered_analysis_df = filtered_analysis_df[
            (filtered_analysis_df["created"].dt.date >= start_date)
            & (filtered_analysis_df["created"].dt.date <= end_date)
        ]

    if issue_types.value:
        filtered_analysis_df = filtered_analysis_df[
            filtered_analysis_df["issue_type"].isin(issue_types.value)
        ]

    if statuses.value:
        filtered_analysis_df = filtered_analysis_df[
            filtered_analysis_df["status"].isin(statuses.value)
        ]

    # Calculate cycle time for resolved issues
    filtered_resolved_df = filtered_analysis_df[
        filtered_analysis_df["resolved"].notna()
    ].copy()
    if not filtered_resolved_df.empty:
        filtered_resolved_df["cycle_time_days"] = (
            filtered_resolved_df["resolved"] - filtered_resolved_df["created"]
        ).dt.days

    filtered_analysis_df
    return filtered_analysis_df, filtered_resolved_df


@app.cell
def __(filtered_analysis_df, mo, px):
    mo.md("## Team Velocity Analysis")

    if filtered_analysis_df.empty:
        mo.md("No data available for velocity analysis.")
    else:
        # Story points by sprint/month
        velocity_df = filtered_analysis_df[
            filtered_analysis_df["story_points"].notna()
        ].copy()

        if not velocity_df.empty:
            # Group by month for velocity tracking
            velocity_df["month"] = velocity_df["resolved"].dt.to_period("M").astype(str)
            monthly_velocity = (
                velocity_df.groupby(["project_key", "month"])["story_points"]
                .sum()
                .reset_index()
            )

            # Velocity trend chart
            fig_velocity = px.line(
                monthly_velocity,
                x="month",
                y="story_points",
                color="project_key",
                title="Team Velocity Trend (Story Points per Month)",
                labels={"story_points": "Story Points", "month": "Month"},
            )
            fig_velocity.update_layout(height=400)

            mo.ui.plotly(fig_velocity)
        else:
            mo.md("No story points data available for velocity analysis.")
    return fig_velocity, monthly_velocity, velocity_df


@app.cell
def __(filtered_analysis_df, mo, px):
    mo.md("## Estimation Accuracy Analysis")

    if filtered_analysis_df.empty:
        mo.md("No data available for estimation accuracy analysis.")
    else:
        # Story points vs cycle time analysis
        estimation_df = filtered_analysis_df[
            (filtered_analysis_df["story_points"].notna())
            & (filtered_analysis_df["resolved"].notna())
        ].copy()

        if not estimation_df.empty:
            estimation_df["cycle_time_days"] = (
                estimation_df["resolved"] - estimation_df["created"]
            ).dt.days

            # Scatter plot: Story Points vs Cycle Time
            fig_estimation = px.scatter(
                estimation_df,
                x="story_points",
                y="cycle_time_days",
                color="issue_type",
                hover_data=["key", "summary"],
                title="Estimation Accuracy: Story Points vs Actual Cycle Time",
                labels={
                    "story_points": "Story Points (Estimate)",
                    "cycle_time_days": "Cycle Time (Days)",
                },
            )
            fig_estimation.update_layout(height=500)

            mo.ui.plotly(fig_estimation)
        else:
            mo.md(
                "No data available with both story points and resolution dates for estimation accuracy analysis."
            )
    return estimation_df, fig_estimation


@app.cell
def __(filtered_analysis_df, go, make_subplots, mo):
    mo.md("## Issue Distribution Analysis")

    if not filtered_analysis_df.empty:
        # Create subplots for various distributions
        fig_dist = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Issues by Status",
                "Issues by Type",
                "Issues by Priority",
                "Issues by Project",
            ),
            specs=[
                [{"type": "pie"}, {"type": "pie"}],
                [{"type": "pie"}, {"type": "pie"}],
            ],
        )

        # Status distribution
        status_counts = filtered_analysis_df["status"].value_counts()
        fig_dist.add_trace(
            go.Pie(
                labels=status_counts.index, values=status_counts.values, name="Status"
            ),
            row=1,
            col=1,
        )

        # Type distribution
        type_counts = filtered_analysis_df["issue_type"].value_counts()
        fig_dist.add_trace(
            go.Pie(labels=type_counts.index, values=type_counts.values, name="Type"),
            row=1,
            col=2,
        )

        # Priority distribution
        priority_counts = filtered_analysis_df["priority"].value_counts()
        fig_dist.add_trace(
            go.Pie(
                labels=priority_counts.index,
                values=priority_counts.values,
                name="Priority",
            ),
            row=2,
            col=1,
        )

        # Project distribution
        project_counts = filtered_analysis_df["project_key"].value_counts()
        fig_dist.add_trace(
            go.Pie(
                labels=project_counts.index,
                values=project_counts.values,
                name="Project",
            ),
            row=2,
            col=2,
        )

        fig_dist.update_layout(height=600, showlegend=False)

        mo.ui.plotly(fig_dist)
    else:
        mo.md("No data available for distribution analysis.")
    return fig_dist, priority_counts, project_counts, status_counts, type_counts


@app.cell
def __(filtered_analysis_df, mo, px, filtered_resolved_df):
    mo.md("## Cycle Time Analysis")

    if not filtered_resolved_df.empty:
        # Box plot of cycle times by issue type
        fig_cycle = px.box(
            filtered_resolved_df,
            x="issue_type",
            y="cycle_time_days",
            title="Cycle Time Distribution by Issue Type",
            labels={"cycle_time_days": "Cycle Time (Days)", "issue_type": "Issue Type"},
        )
        fig_cycle.update_layout(height=400)

        # Cycle time trend over time
        cycle_trend_df = filtered_resolved_df.copy()
        cycle_trend_df["resolved_month"] = (
            cycle_trend_df["resolved"].dt.to_period("M").astype(str)
        )
        cycle_avg_time = (
            cycle_trend_df.groupby("resolved_month")["cycle_time_days"]
            .mean()
            .reset_index()
        )

        fig_cycle_trend = px.line(
            cycle_avg_time,
            x="resolved_month",
            y="cycle_time_days",
            title="Average Cycle Time Trend",
            labels={
                "cycle_time_days": "Average Cycle Time (Days)",
                "resolved_month": "Month",
            },
        )
        fig_cycle_trend.update_layout(height=400)

        mo.vstack([mo.ui.plotly(fig_cycle), mo.ui.plotly(fig_cycle_trend)])
    else:
        mo.md("No resolved issues available for cycle time analysis.")
    return cycle_avg_time, cycle_trend_df, fig_cycle, fig_cycle_trend


@app.cell
def __(filtered_analysis_df, mo):
    mo.md("## Key Metrics Summary")

    if not filtered_analysis_df.empty:
        # Calculate key metrics
        summary_total_issues = len(filtered_analysis_df)
        summary_resolved_issues = len(
            filtered_analysis_df[filtered_analysis_df["resolved"].notna()]
        )
        summary_resolution_rate = (
            (summary_resolved_issues / summary_total_issues * 100)
            if summary_total_issues > 0
            else 0
        )

        summary_avg_story_points = (
            filtered_analysis_df["story_points"].mean()
            if "story_points" in filtered_analysis_df.columns
            else 0
        )
        summary_total_story_points = (
            filtered_analysis_df["story_points"].sum()
            if "story_points" in filtered_analysis_df.columns
            else 0
        )

        summary_avg_cycle_time = (
            filtered_analysis_df[filtered_analysis_df["resolved"].notna()][
                "cycle_time_days"
            ].mean()
            if "cycle_time_days" in filtered_analysis_df.columns
            else 0
        )

        mo.md(
            f"""
        ### 📊 Key Performance Indicators
        
        - **Total Issues**: {summary_total_issues:,}
        - **Resolved Issues**: {summary_resolved_issues:,} ({summary_resolution_rate:.1f}%)
        - **Total Story Points**: {summary_total_story_points:.0f}
        - **Average Story Points per Issue**: {summary_avg_story_points:.1f}
        - **Average Cycle Time**: {summary_avg_cycle_time:.1f} days
        
        ### 📈 Insights for ScrumMasters & Product Owners
        
        - Use the velocity trend to plan future sprints
        - Monitor estimation accuracy to improve planning precision
        - Track cycle time to identify process bottlenecks
        - Analyze issue distribution to balance workload
        - Refresh data regularly to maintain current insights
        """
        )
    else:
        mo.md("No data available for metrics calculation.")
    return (
        summary_avg_cycle_time,
        summary_avg_story_points,
        summary_resolution_rate,
        summary_resolved_issues,
        summary_total_issues,
        summary_total_story_points,
    )


@app.cell
def __(log_df, mo, pd):
    # Extraction history section
    mo.md("## 📋 Data Extraction History")

    if not log_df.empty:
        # Format the log for display
        display_log = log_df.copy()
        if "extraction_time" in display_log.columns:
            display_log["extraction_time"] = pd.to_datetime(
                display_log["extraction_time"]
            ).dt.strftime("%Y-%m-%d %H:%M:%S")

        # Show recent extractions
        recent_extractions = display_log.head(10)[
            [
                "project_key",
                "start_date",
                "end_date",
                "issues_extracted",
                "extraction_time",
            ]
        ]

        mo.ui.table(recent_extractions, label="Recent Data Extractions (Last 10)")
    else:
        mo.md("No extraction history available.")
    return display_log, recent_extractions


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
