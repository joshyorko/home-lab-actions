# Build stage - contains all build tools and dependencies
FROM debian:bookworm-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl

# Download and extract Rancher CLI
ADD https://releases.rancher.com/cli2/v2.11.3/rancher-linux-amd64-v2.11.3.tar.gz rancher-cli.tar.gz
RUN tar -xzf rancher-cli.tar.gz \
    && mv rancher-v2.11.3/rancher /usr/local/bin/rancher \
    && chmod +x /usr/local/bin/rancher \
    && rm -rf rancher-cli.tar.gz rancher-v2.11.3

# Download Action Server
ADD https://cdn.sema4.ai/action-server/releases/2.14.0/linux64/action-server /usr/local/bin/action-server
RUN chmod +x /usr/local/bin/action-server

# Runtime stage - minimal image with only runtime dependencies
FROM debian:bookworm-slim AS runtime

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    procps \
    nginx \
    supervisor \
    sudo \
    openssl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy binaries from builder stage
COPY --from=builder /usr/local/bin/kubectl /usr/local/bin/kubectl
COPY --from=builder /usr/local/bin/rancher /usr/local/bin/rancher
COPY --from=builder /usr/local/bin/action-server /usr/local/bin/action-server

# Copy configuration files
COPY config/nginx.conf /etc/nginx/nginx.conf
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Setup user and permissions
RUN useradd -m as-user \
    && chown -R as-user:as-user /var/log /run /var/lib/nginx

# Setup workspace
RUN mkdir -p /action-server/datadir /action-server/actions \
    && chown -R as-user:as-user /action-server

# Ensure /home/as-user/.rancher exists and is owned by as-user
RUN mkdir -p /home/as-user/.rancher \
    && chown -R as-user:as-user /home/as-user/.rancher

# Setup sudo permissions for certificate generation
RUN echo 'Defaults env_keep += "TLS_CRT TLS_KEY SERVER_URL"' | tee -a /etc/sudoers \
    && echo "as-user ALL=(ALL) NOPASSWD:SETENV: /action-server/generate-certs.sh" | tee -a /etc/sudoers

WORKDIR /action-server/actions

# Copy application files
COPY . .

# Add script to generate TLS certificates from environment variables
COPY generate-certs.sh /action-server/generate-certs.sh
RUN chmod +x /action-server/generate-certs.sh

# Switch to non-root user and import actions
USER as-user
RUN action-server import --datadir=/action-server/datadir

EXPOSE 8080 443 80

CMD ["/usr/bin/supervisord"]