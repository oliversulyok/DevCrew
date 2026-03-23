#!/bin/bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AI Stack Setup...${NC}"

# 1. Check for NVIDIA Container Toolkit
if ! dpkg -l | grep -q nvidia-container-toolkit; then
    echo -e "${YELLOW}Warning: nvidia-container-toolkit not found!${NC}"
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Please install nvidia-container-toolkit first. Exiting.${NC}"
        echo "Refer to: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html"
        exit 1
    fi
else
    echo -e "${GREEN}NVIDIA Container Toolkit detected.${NC}"
fi

# 2. Directory Structure and Permissions
echo -e "${GREEN}Creating directories and setting permissions...${NC}"
DIRS=("ollama_data" "n8n_data" "qdrant_data" "postgres_data")

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "Created $dir"
    fi
done

# Set strict permissions
# Requirements: "ensure the Docker group has access, but restrict global read/write"
# Current user should own it, group should be docker.
if getent group docker >/dev/null; then
    chown -R "$USER:docker" .
    chmod -R 770 .
    echo "Permissions set to 770 and owner $USER:docker"
else
    echo -e "${YELLOW}Docker group not found. Setting permissions to 700 for current user.${NC}"
    chmod -R 700 .
fi

# 3. Generate .env file
if [ ! -f .env ]; then
    echo -e "${GREEN}Generating .env file with secure secrets...${NC}"
    
    # Generate random secrets
    PG_PASSWORD=$(openssl rand -hex 16)
    N8N_PASSWORD=$(openssl rand -hex 16)
    N8N_ENC_KEY=$(openssl rand -hex 16)
    QDRANT_KEY=$(openssl rand -hex 16)
    
    cat > .env <<EOF
# Postgres Configuration
POSTGRES_USER=n8n_user
POSTGRES_PASSWORD=${PG_PASSWORD}
POSTGRES_DB=n8n_db

# n8n Configuration
N8N_AUTH_USER=admin
N8N_AUTH_PASSWORD=${N8N_PASSWORD}
N8N_ENCRYPTION_KEY=${N8N_ENC_KEY}

# Qdrant Configuration
QDRANT_API_KEY=${QDRANT_KEY}

# Timezone
GENERIC_TIMEZONE=UTC
EOF
    echo -e "${GREEN}.env file created.${NC}"
    echo -e "Credentials saved in .env"
else
    echo -e "${YELLOW}.env file already exists. Skipping generation.${NC}"
fi

# 4. Start Services
echo -e "${GREEN}Starting Docker services...${NC}"
docker compose up -d

# 5. Pull Ollama Models
echo -e "${GREEN}Waiting for Ollama to initialize...${NC}"
# Wait loop to ensure ollama is ready
timeout=60
elapsed=0
while ! docker exec ollama ollama list >/dev/null 2>&1; do
    sleep 2
    elapsed=$((elapsed+2))
    if [ $elapsed -ge $timeout ]; then
        echo -e "${RED}Ollama failed to start within timeout.${NC}"
        exit 1
    fi
done

echo -e "${GREEN}Pulling AI models (llama3.1, llava)...${NC}"
echo "This might take a while depending on your internet connection."

docker exec ollama ollama pull llama3.1
docker exec ollama ollama pull llava

echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "n8n is available at: http://localhost:5678"
echo -e "Your credentials are in the .env file."
