# 🛡️ Option 2 Setup Guide: SonarQube Quality Gates Integration

This guide provides step-by-step instructions and professional AI-driven workflows to connect your ISF-Core engine with a SonarQube server. Integrating SonarQube enables automated static code analysis, continuous quality tracking, and self-healing of code quality and security issues.

## Why Integrate SonarQube with ISF-Core?
* **Continuous Hygiene:** Automatically run security and bug audits on generated or modified code.
* **Auto-Healing Loops:** When SonarQube flags an issue (e.g., resource leak, dead code, broad exceptions), ISF-Core fetches the warning details via the SonarQube Web API, designs a fix, implements it, and verifies it.
* **Quality Gate Enforcement:** Restrict builds or branch merges from going green if test coverage is below your team's threshold or if critical code smells exist.

---

## Step 1: Deploy SonarQube

We support two deployment methods: **Docker Compose (Recommended - Persistent)** and **Standalone Container (Quick Test - Volatile)**.

### Deploy via Docker Compose
This method spins up SonarQube alongside a dedicated, persistent PostgreSQL database, ensuring you do not lose your scan history, custom quality gates, or user tokens when containers are updated or restarted.

1. Open your `compose.yml` (and/or `compose.mac.yml`) and ensure the `sonardb` and `sonarqube` services are defined under `services:`:

```yaml
  # SonarQube Database
  sonardb:
    image: postgres:15
    container_name: sonardb
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=${SONAR_DB_USER:-sonar}
      - POSTGRES_PASSWORD=${SONAR_DB_PASSWORD:-sonar_secure_pass}
      - POSTGRES_DB=sonarqube
    volumes:
      - sonarqube_db:/var/lib/postgresql/data

  # SonarQube Server
  sonarqube:
    image: sonarqube:community
    container_name: sonarqube
    restart: unless-stopped
    depends_on:
      - sonardb
    ports:
      - "9000:9000"
    environment:
      - SONAR_JDBC_URL=jdbc:postgresql://sonardb:5432/sonarqube
      - SONAR_JDBC_USERNAME=${SONAR_DB_USER:-sonar}
      - SONAR_JDBC_PASSWORD=${SONAR_DB_PASSWORD:-sonar_secure_pass}
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
      - sonarqube_logs:/opt/sonarqube/logs
```

2. Verify that the named volumes are defined at the bottom of your `compose.yml`:

```yaml
volumes:
  sonarqube_db:
  sonarqube_data:
  sonarqube_extensions:
  sonarqube_logs:
```

3. Launch the SonarQube stack:
```bash
docker compose up -d sonardb sonarqube
```

---

## Step 2: Configure the SonarQube Admin Console

Once the container is running:
1. Navigate to `http://localhost:9000` on your host machine.
2. Log in using the default credentials:
   * **Username:** `admin`
   * **Password:** `admin`
3. You will be prompted to change the default password. Update it securely.
4. **Create your project:**
   * Click the **Create Project** button (choose **Manually**).
   * Enter a project display name and define a unique **Project Key** (e.g., `isf_core_applications`). Save this key as you will need it for your environment configuration.
5. **Generate a Global Analysis Token:**
   * Go to **My Account > Security**.
   * Under **Generate Token**, enter a name (e.g., `isf_core_token`).
   * Select the token type: Choose **Global Analysis** (this is highly recommended for automated static scanners).
   * Click **Generate** and copy the generated token immediately (you will not be able to see it again).
6. Go to **Administration > Security** and toggle **Force user authentication** to **OFF** (this allows local scanning tools to submit initial analysis reports without anonymous blockages).

---

## Step 3: Configure Environment Variables

Update your `.env` file at the root of your project directory to include your SonarQube credentials and database configuration:

1. Open your `.env` file:
   ```bash
   nano .env
   ```
2. Add/uncomment the following parameters:
   ```env
   # SonarQube Database Settings (Required if using Docker Compose Option A)
   SONAR_DB_USER=sonar
   SONAR_DB_PASSWORD=sonar_secure_pass

   # SonarQube Connection Settings
   # Note: Use 'http://sonarqube:9000' inside the docker bridge network, or 'http://localhost:9000' if running standalone on Host OS.
   SONAR_URL=http://sonarqube:9000
   SONAR_TOKEN=your_generated_sonarqube_user_token_here
   SONAR_PROJECT_KEY=isf_core_applications
   ```

---

## Step 4: Configure the Auto-Healer Module

ISF-Core contains an automated routine inside its background tasks. To let the agent fetch and repair SonarQube-reported issues:

1. Ensure the `sonar-issues` execution task is registered in your `cron_scheduled_jobs` table.
2. The task operates by fetching issues categorized as `BUG`, `VULNERABILITY`, or `CODE_SMELL` for your specified project key, grouping them by file path, and assigning a coding agent to resolve them.

---

## Step 5: Run a Test Scan

To test the integration, you can manually trigger a scan using the static analysis tool inside the interactive workspace console or via your terminal inside the Docker container:

```bash
docker compose exec isf-core python -m backend.tasks.sonar_scanner --project isf_core_applications
```

Navigate to your local SonarQube dashboard (`http://localhost:9000`) to confirm that your project data, lines of code, and quality ratings have populated successfully!

---

## 🤖 AI Pro-Tips: Developing with SonarQube & ISF-Core

Developing inside an agentic, test-driven engine like ISF-Core offers unique advantages. Here are the professional guidelines for using AI to manage your SonarQube integration and auto-healing features.

### 1. Let the AI Autonomously Update Your Compose Files
Instead of editing YAML files manually, you can instruct your developer AI to cleanly inject the service definition, network rules, and container environment variables. 

**Recommended Prompt for the AI Developer:**
```text
Please integrate the SonarQube and Sonar DB services into our project structure:

1. Locate and modify `compose.yml` and `compose.mac.yml`:
   a. Under `services:`, add a persistent PostgreSQL database service named `sonardb` (image postgres:15) with ports mapped to "5432:5432" and volume "sonarqube_db" mapped to "/var/lib/postgresql/data". Use the variables ${SONAR_DB_USER} and ${SONAR_DB_PASSWORD} for environment configuration.
   b. Add the `sonarqube` service (image sonarqube:community) with port 9000 mapped, depending on `sonardb`. Use persistent volumes: "sonarqube_data", "sonarqube_extensions", and "sonarqube_logs". Configure the JDBC URL environment variable: "SONAR_JDBC_URL=jdbc:postgresql://sonardb:5432/sonarqube".
   c. At the root level of both files, ensure the following keys are added to the `volumes:` block:
      - sonarqube_db:
      - sonarqube_data:
      - sonarqube_extensions:
      - sonarqube_logs:
   d. In the environment variables for the main `isf-core` container, uncomment:
      - SONAR_PROJECT_KEY=${SONAR_PROJECT_KEY}
      - SONAR_URL=http://sonarqube:9000
      - SONAR_TOKEN=${SONAR_TOKEN}

2. Locate `.env.example` (or similar templates in the root) and add variables for:
   - SONAR_DB_USER=sonar
   - SONAR_DB_PASSWORD=sonar_secure_pass
   - SONAR_URL=http://sonarqube:9000
   - SONAR_TOKEN=
   - SONAR_PROJECT_KEY=isf_core_applications

Ensure the YAML structures are perfectly formatted with spaces, all dependencies are explicitly satisfied, and no existing services or environment keys are corrupted or removed.
```

### 2. Configure a Real-Time Auto-Healing Test Loop
When using the Red-Green-Refactor loop (`Agentic_Testing_TDA_Protocol.md`), you can program the AI to run static analysis directly on your feature branch before proposing changes:

1. Let the AI implement the feature.
2. Command the AI to run the local sonar scanner command:
   ```bash
   docker compose exec -T isf-core python -m backend.tasks.sonar_scanner --file backend/routers/chat.py
   ```
3. Use the AI to query the local SonarQube Web API (`GET /api/issues/search`) to see if any new Code Smells or Vulnerabilities were introduced by the changes.
4. If the Sonar API returns issues, feed the JSON details back to the LLM context and let it refactor the code automatically until `GET /api/issues/search` returns an empty list.

This guarantees that no dirty code ever reaches your pull requests!
