import sys
import platform
import subprocess
from pathlib import Path

def main():
    print("🛑 Shutting down ISF-Core...")

    # 1. Detect OS and pick compose file
    is_mac = platform.system().lower() == "darwin"
    compose_file = "compose.mac.yml" if is_mac else "compose.yml"

    if not Path(compose_file).exists():
        print(f"❌ Error: {compose_file} not found in current directory.")
        sys.exit(1)

    # 2. Gracefully stop and remove containers
    print(f"\n🔄 Stopping containers using {compose_file}...")
    result = subprocess.run(["docker", "compose", "-f", compose_file, "down"])

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("✅ ISF-Core & AI-Proxy Stopped Successfully!")
        print("   All containers have been shut down.")
        print("   Your data is preserved in the 'data/' directory.")
        print("   To restart, run: python start_isf_core.py")
        print("=" * 50 + "\n")
    else:
        print("\n❌ Failed to stop containers. Please check the Docker logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
