# TruthGuards

**RAG-based guardrail retrieval system for AI agents**

TruthGuards helps mitigate LLM hallucinations by storing and retrieving relevant textual guardrails based on the prompt being processed. Instead of adding all guardrails to every prompt (which is overwhelming and inefficient), only the most relevant ones are retrieved using hybrid search.

## Features

- **Hybrid Search**: Combines BM25 keyword search with semantic vector search for optimal retrieval
- **Model-Specific Guardrails**: Guardrails are filtered by LLM model name
- **Multiple Interfaces**: REST API, MCP server, and Streamlit web UI
- **Self-Contained**: Uses Weaviate with built-in transformers for embeddings (no external API keys needed)
- **Docker Ready**: Single command deployment with Docker Compose

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/truthguards.git
cd truthguards

# Start all services
docker-compose up -d

# Access the services:
# - Web UI: http://localhost:8501
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Weaviate (requires Docker)
docker-compose up -d weaviate t2v-transformers

# Set Python path
export PYTHONPATH=$PWD/src

# Run the API
python -m uvicorn truthguards.api.main:app --reload

# In another terminal, run Streamlit
streamlit run src/truthguards/ui/streamlit_app.py
```

## API Reference

### Add Guardrail

```bash
POST /guardrails
Content-Type: application/json

{
  "prompt": "What is the capital of France?",
  "model_name": "gpt-4",
  "guardrails": "Always verify factual information before responding. If uncertain, state that the information should be verified."
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Guardrail created successfully"
}
```

### Search Guardrails

```bash
POST /guardrails/search
Content-Type: application/json

{
  "prompt": "Tell me about the French Revolution",
  "model_name": "gpt-4",
  "limit": 5
}
```

Response:
```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "prompt": "What is the capital of France?",
      "model_name": "gpt-4",
      "guardrails": "Always verify factual information...",
      "score": 0.85
    }
  ],
  "count": 1
}
```

### Other Endpoints

- `GET /health` - Health check
- `GET /models` - List available models
- `GET /guardrails/{id}` - Get guardrail by ID
- `DELETE /guardrails/{id}` - Delete guardrail

Full API documentation available at `/docs` when the server is running.

## MCP Integration

TruthGuards exposes an MCP server for integration with AI assistants like Claude.

### Configuration

Add to your Claude Desktop config (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "truthguards": {
      "command": "python",
      "args": ["-m", "truthguards.mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/truthguards/src"
      }
    }
  }
}
```

### Available Tools

1. **add_guardrail** - Add a new guardrail to the database
   - `prompt`: The prompt pattern this guardrail applies to
   - `model_name`: The LLM model (e.g., "gpt-4", "claude-3-opus")
   - `guardrails`: The guardrail text

2. **search_guardrails** - Find relevant guardrails
   - `prompt`: The prompt to search for
   - `model_name`: Filter by model
   - `limit`: Maximum results (default: 5)

## Configuration

Configuration is stored in `config/config.yaml`:

```yaml
# Available LLM models
models:
  - gpt-4
  - gpt-4-turbo
  - claude-3-opus
  - claude-3-sonnet
  # Add more models as needed

# Weaviate connection
weaviate:
  host: "localhost"
  port: 8080
  grpc_port: 50051

# Hybrid search settings
search:
  default_limit: 5
  alpha: 0.5  # 0 = pure keyword, 1 = pure vector
```

Environment variables can override config values with prefix `TRUTHGUARDS_`.

## How Hybrid Search Works

TruthGuards uses Weaviate's hybrid search which combines:

1. **BM25 (Keyword Search)**: Finds exact term matches
2. **Vector Search (Semantic)**: Finds semantically similar content

The `alpha` parameter controls the balance:
- `alpha=0`: Pure keyword search
- `alpha=0.5`: Balanced (default)
- `alpha=1`: Pure vector search

## Project Structure

```
truthguards/
├── src/truthguards/
│   ├── api/           # FastAPI REST API
│   ├── core/          # Core logic (config, Weaviate client)
│   ├── mcp/           # MCP server
│   └── ui/            # Streamlit web interface
├── config/            # Configuration files
├── tests/             # Pytest tests
├── Dockerfile         # Container image
└── docker-compose.yaml
```

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Use Cases

1. **AI Agent Enhancement**: Query TruthGuards before processing user prompts to get relevant guardrails
2. **Collaborative Knowledge Base**: Teams can contribute guardrails that benefit all users
3. **Model-Specific Instructions**: Different models may need different guardrails for the same type of question
4. **On-Premise Deployment**: Run locally for sensitive/private guardrail data

## Example Workflow

```python
import httpx

# 1. Add a guardrail
httpx.post("http://localhost:8000/guardrails", json={
    "prompt": "Questions about medical symptoms",
    "model_name": "gpt-4",
    "guardrails": "I am not a medical professional. Always recommend consulting a healthcare provider for medical advice."
})

# 2. Before processing a user prompt, search for relevant guardrails
response = httpx.post("http://localhost:8000/guardrails/search", json={
    "prompt": "I have a headache, what should I do?",
    "model_name": "gpt-4"
})

# 3. Add retrieved guardrails to your system prompt
guardrails = response.json()["results"]
system_prompt = "You are a helpful assistant.\n\n"
for g in guardrails:
    system_prompt += f"GUARDRAIL: {g['guardrails']}\n"
```

## AWS EC2 Deployment

Step-by-step guide to deploy TruthGuards on AWS EC2.

### Prerequisites

- AWS account
- AWS CLI configured (optional, for command-line setup)
- SSH key pair for EC2 access

### Step 1: Launch EC2 Instance

1. **Log in to AWS Console** and navigate to EC2

2. **Click "Launch Instance"**

3. **Configure the instance:**
   - **Name**: `truthguards-server`
   - **AMI**: Ubuntu Server 24.04 LTS (or Amazon Linux 2023)
   - **Instance type**: `t3.medium` (minimum) or `t3.large` (recommended)
     - The transformer model requires ~2GB RAM
     - `t3.medium`: 2 vCPU, 4GB RAM - works but tight
     - `t3.large`: 2 vCPU, 8GB RAM - recommended
   - **Key pair**: Select or create a key pair for SSH access
   - **Storage**: 20GB gp3 (minimum)

4. **Configure Security Group** (Network settings → Edit):

   | Type | Port | Source | Description |
   |------|------|--------|-------------|
   | SSH | 22 | Your IP | SSH access |
   | Custom TCP | 8000 | 0.0.0.0/0 | API |
   | Custom TCP | 8501 | 0.0.0.0/0 | Web UI |
   | Custom TCP | 8080 | 0.0.0.0/0 | Weaviate (optional) |

5. **Launch the instance** and wait for it to be running

6. **Note the Public IPv4 address** (e.g., `54.123.45.67`)

### Step 2: Connect to EC2 Instance

```bash
# Make sure your key file has correct permissions
chmod 400 your-key.pem

# Connect via SSH
ssh -i your-key.pem ubuntu@<your-ec2-public-ip>

# For Amazon Linux, use:
# ssh -i your-key.pem ec2-user@<your-ec2-public-ip>
```

### Step 3: Install Docker

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose-v2

# Add current user to docker group (to run docker without sudo)
sudo usermod -aG docker $USER

# Apply group changes (or logout and login again)
newgrp docker

# Verify Docker is working
docker --version
docker compose version
```

### Step 4: Clone and Deploy TruthGuards

```bash
# Clone the repository
git clone https://github.com/yourusername/truthguards.git
cd truthguards

# Start all services (this will take a few minutes on first run)
docker compose up -d

# Check that all containers are running
docker compose ps

# View logs (optional)
docker compose logs -f
```

### Step 5: Verify Deployment

```bash
# Wait ~30 seconds for services to initialize, then check health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","weaviate_connected":true}

# Test adding a guardrail
curl -X POST http://localhost:8000/guardrails \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test prompt", "model_name": "gpt-4", "guardrails": "Test guardrail"}'
```

### Step 6: Access from Your Browser

Replace `<your-ec2-public-ip>` with your actual EC2 public IP:

- **Web UI**: `http://<your-ec2-public-ip>:8501`
- **API**: `http://<your-ec2-public-ip>:8000`
- **API Docs**: `http://<your-ec2-public-ip>:8000/docs`

### Step 7: (Optional) Set Up Domain with HTTPS

For production, set up a domain with SSL using nginx as a reverse proxy:

```bash
# Install nginx and certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Create nginx config
sudo tee /etc/nginx/sites-available/truthguards << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/truthguards /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com
```

### Step 8: (Optional) Auto-start on Reboot

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Create systemd service for TruthGuards
sudo tee /etc/systemd/system/truthguards.service << EOF
[Unit]
Description=TruthGuards
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/truthguards
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl enable truthguards
```

### Troubleshooting

**Services not starting:**
```bash
# Check container logs
docker compose logs truthguards
docker compose logs weaviate

# Restart services
docker compose restart
```

**Out of memory:**
```bash
# Check memory usage
free -h
docker stats

# If OOM, upgrade to a larger instance type (t3.large or t3.xlarge)
```

**Cannot connect from browser:**
- Verify security group allows inbound traffic on ports 8000 and 8501
- Check that the instance has a public IP
- Ensure services are running: `docker compose ps`

**Weaviate not connecting:**
```bash
# Weaviate takes ~30-60 seconds to initialize with transformer model
# Check if it's ready:
curl http://localhost:8080/v1/.well-known/ready

# Check transformer service:
docker compose logs t2v-transformers
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
