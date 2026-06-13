# 🛡️ Option 2 Setup Guide: SonarQube Quality Gates Integration

This guide provides instructions to connect your ISF-Core engine with a SonarQube server to enable automated static code analysis, continuous quality tracking, and self-healing of code quality issues.

## Why Integrate SonarQube?
* **Continuous Hygiene:** Automatically run security and bug audits on generated code.
* **Auto-Healing Loops:** When SonarQube flags an issue (e.g., resource leak, dead code, broad exceptions), ISF-Core fetches the warning details via API and rewrites the code to clear the issue.
* **Quality Gate Enforcement:** Restrict builds or notifications from going green if test coverage is below your team's threshold or if critical smells exist.

---

## Step 1: Deploy SonarQube (or use a Cloud Instance)

If you are running SonarQube locally via Docker, you can run a standalone container:

```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
```

Once running:
1. Navigate to `http://localhost:9000` (Default credentials are `admin` / `admin`, you will be prompted to change them).
2. Go to **My Account > Security** and generate a new **User Token** named `isf_core_token`. Copy this token.

---

## Step 2: Configure Environment Variables

Update your `.env` file at the root of your `isf-core` directory to include your SonarQube credentials:

1. Open `.env`:
   ```bash
   nano .env
   ```
2. Add the following SonarQube parameters:
   ```env
   # SonarQube Quality Gates
   SONAR_URL=http://localhost:9000
   SONAR_TOKEN=your_generated_sonarqube_token_here
   SONAR_PROJECT_KEY=isf_core_applications
   ```

---

## Step 3: Configure the Auto-Healer Module

ISF-Core contains an automated routine inside its background tasks. To let the agent fetch and repair SonarQube-reported issues:

1. Ensure the `sonar-issues` execution task is registered in your `cron_scheduled_jobs` table.
2. The task operates by fetching issues categorized as `BUG`, `VULNERABILITY`, or `CODE_SMELL` for your specified project key, grouping them by file path, and assigning a coding agent to resolve them.

---

## Step 4: Run a Test Scan

To test the integration, you can manually run a scan using the static analysis tool inside the interactive workspace console or via your terminal inside the Docker container:

```bash
docker compose exec isf-core-engine python -m backend.tasks.sonar_scanner --project isf_core_applications
```

Navigate to your local SonarQube dashboard (`http://localhost:9000`) to confirm that your project data, lines of code, and quality ratings have populated successfully!
