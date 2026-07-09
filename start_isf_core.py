import sys
import platform
import subprocess
from pathlib import Path

def main():
    print("🚀 Starting ISF-Core...")
    
    # 1. Prerequisite check: Docker
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Docker is not running or not installed.")
        print("Please ensure Docker Desktop (or Docker Engine) is running and try again.")
        sys.exit(1)

    # 2. Check .env exists
    if not Path(".env").exists():
        print("⚠️ Warning: '.env' file is missing. Please run 'python setup.py' first.")
        sys.exit(1)

    # 3. Detect OS and pick compose file
    is_mac = platform.system().lower() == "darwin"
    compose_file = "compose.mac.yml" if is_mac else "compose.yml"
    
    if not Path(compose_file).exists():
        print(f"❌ Error: {compose_file} not found in current directory.")
        sys.exit(1)

    # 4. Execute compose commands
    print("\n🔄 Pulling latest images from Docker Hub (this may take a moment)...")
    subprocess.run(["docker", "compose", "--env-file", ".env", "-f", compose_file, "pull"])

    print(f"\n🚀 Starting containers using {compose_file}...")
    result = subprocess.run(["docker", "compose", "--env-file", ".env", "-f", compose_file, "up", "-d"])
    
    if result.returncode == 0:
        print("\n" + "="*50)
        print("🎉 ISF-Core & AI-Proxy Started Successfully!")
        print("👉 Dashboard URL: http://localhost:3006")
        print("="*50 + "\n")
    else:
        print("\n❌ Failed to start containers. Please check the Docker logs above.")

if __name__ == "__main__":
    main()