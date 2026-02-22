# =============================================================================
# example.py — Demo/example script for the gherkins deployment library.
#
# This file is NOT production code. It illustrates how to use gherkins to
# automate a typical web-app deployment: clone a repo locally, copy it to a
# remote server over SSH, install dependencies, and start the backend process.
#
# Before running, replace every placeholder value (marked with <...>) with
# your own credentials and paths.  Never commit real credentials to version
# control.
# =============================================================================

import os
from gherkins.Serloc import local_exec, ServerConnection
from gherkins.StageManager import StageManager

# ---------------------------------------------------------------------------
# Configuration — replace placeholder values before running
# ---------------------------------------------------------------------------
REPO_URL         = "https://github.com/<your-username>/<your-repo>.git"
SERVER_IP        = "your.server.ip"
SERVER_USER_NAME = "your_username"

# --- Local paths ---
LOCAL_REPO_DIR   = "./repo"
SECRETS_DIR      = "./secrets"
SSH_KEY_PATH     = "./credentials/ssh_key.pem"
NGINX_CONF_PATH  = "./nginx.conf"

# --- Remote paths ---
REMOTE_APP_DIR    = "/opt/app"
REMOTE_TEMP_DIR   = f"/home/{SERVER_USER_NAME}/temp"
REMOTE_CONFIG_DIR = "/etc/nginx/sites-available"

# ---------------------------------------------------------------------------
# Deployment pipeline
# ---------------------------------------------------------------------------
sm     = StageManager()
server = ServerConnection(SERVER_IP, SERVER_USER_NAME, SSH_KEY_PATH)

# @sm.stage("Git pull code to local machine")
def stage_1():
    # Clone repo locally if not already cloned
    if not os.path.exists(LOCAL_REPO_DIR):
        local_exec(f"git clone {REPO_URL} {LOCAL_REPO_DIR}")
    else:
        print("Repo already cloned. Pulling instead.")
        local_exec(
            f"""
            cd {LOCAL_REPO_DIR}
            git pull
            """)

# @sm.stage("Install dependencies on server")
def install_dependencies_remote():
    server.exec(
        f"""
        sudo apt update
        sudo apt upgrade -y
        sudo apt install -y python3 python3-pip python3-venv
        """)

@sm.stage("Clear existing files on server (if any)")
def stage_2():
    server.exec(
    f"""
        rm -rf {REMOTE_TEMP_DIR}
        sudo rm -rf {REMOTE_APP_DIR}/* {REMOTE_APP_DIR}/.*
        sudo rm -f /etc/ssl/certs/cert.crt /etc/ssl/private/key.key
    """)

@sm.stage("Copy code files to server")
def stage_3():
    server.scp(LOCAL_REPO_DIR, REMOTE_TEMP_DIR)
    server.exec(
    f"""
        sudo mv {REMOTE_TEMP_DIR}/* {REMOTE_TEMP_DIR}/.* {REMOTE_APP_DIR}
        sudo rmdir {REMOTE_TEMP_DIR}
    """)

@sm.stage("Install requirements.txt")
def stage_4():
    server.exec(
    f"""
        cd {REMOTE_APP_DIR}/backend
        sudo python3 -m venv .venv
        sudo .venv/bin/pip install -r requirements.txt
    """)

@sm.stage("Copy secrets to server")
def stage_copy_secrets():
    server.scp(SECRETS_DIR, REMOTE_TEMP_DIR)
    server.exec(f"""
        sudo cp {REMOTE_TEMP_DIR}/client_secret.json {REMOTE_APP_DIR}/backend/client_secret.json
        sudo cp {REMOTE_TEMP_DIR}/.env {REMOTE_APP_DIR}/backend/.env
        sudo cp {REMOTE_TEMP_DIR}/cert.crt /etc/ssl/certs/cert.crt
        sudo cp {REMOTE_TEMP_DIR}/key.key /etc/ssl/private/key.key
        sudo chmod 600 /etc/ssl/private/key.key
        rm -rf {REMOTE_TEMP_DIR}/secrets
    """
    )

@sm.stage("Configure NGINX")
def stage_nginx():
    server.scp(NGINX_CONF_PATH, f"/home/{SERVER_USER_NAME}/nginx_app.conf")
    server.exec(f"""
        sudo apt install -y nginx
        sudo mv /home/{SERVER_USER_NAME}/nginx_app.conf {REMOTE_CONFIG_DIR}/app
        sudo ln -sf {REMOTE_CONFIG_DIR}/app /etc/nginx/sites-enabled/app
        sudo rm -f /etc/nginx/sites-enabled/default
        sudo nginx -t
        sudo systemctl restart nginx
        sudo systemctl enable nginx
    """)

@sm.stage("Run backend")
def stage_5():
    server.exec(f"""
        cd {REMOTE_APP_DIR}/backend
        pkill -f "uvicorn main:app" || true
        set -a
        . .env
        set +a
        nohup .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
    """)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run deployment stages.")
    parser.add_argument(
        "stages",
        nargs="*",
        metavar="STAGE",
        help="Names of stages to run (default: all stages in order)",
    )
    args = parser.parse_args()

    sm.run(args.stages or None)
