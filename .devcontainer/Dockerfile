FROM python:3.14-slim

# ---------------------
# Install: Git
# ---------------------
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---------------------
# Install: UV
# ---------------------
RUN pip install uv

# ---------------------
# Setup Work Directory
# ---------------------
WORKDIR /workspaces/task-lattice

# ---------------------
# Setup user
# ---------------------
RUN useradd -ms /bin/bash vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER vscode

CMD ["sleep", "infinity"]