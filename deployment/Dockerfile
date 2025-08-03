FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install gh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data and logs directories
RUN mkdir -p /app/data/cycles /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV GITHUB_TOKEN=""
ENV REPO="renatlas/renatlas-identity"

# Configure git (needed for gh CLI)
RUN git config --global user.email "renatlas.dev@gmail.com" \
    && git config --global user.name "Ren Atlas"

# Health check script
COPY deployment/healthcheck.py /app/healthcheck.py

EXPOSE 5000

CMD ["python3", "tools/autonomous-learner.py"]