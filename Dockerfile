FROM debian:bookworm-slim

# Setup Nginx and Supervisor
RUN apt-get update && apt-get install -y procps nginx supervisor && \
    rm -rf /var/lib/apt/lists/*

COPY config/nginx.conf /etc/nginx/nginx.conf
COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Setup user and permissions
RUN useradd -m as-user
RUN chown -R as-user:as-user /var/log /run /var/lib/nginx

# Setup workspace
RUN mkdir -p /action-server/datadir /action-server/actions
RUN chown -R as-user:as-user /action-server

# Install Playwright dependencies and kubectl (required by Rancher CLI)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    libxkbcommon0 \
    libxshmfence1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl

WORKDIR /action-server/actions


# Install Rancher CLI without using /tmp
ADD https://releases.rancher.com/cli2/v2.11.3/rancher-linux-amd64-v2.11.3.tar.gz rancher-cli.tar.gz
RUN tar -xzf rancher-cli.tar.gz && \
    mv rancher-v2.11.3/rancher /usr/local/bin/rancher && \
    chmod +x /usr/local/bin/rancher && \
    rm -rf rancher-cli.tar.gz rancher-v2.11.3

# Ensure /home/as-user/.rancher exists and is owned by as-user (will be a mount in compose, but safe for non-compose runs)
RUN mkdir -p /home/as-user/.rancher && chown -R as-user:as-user /home/as-user/.rancher

# Setup Action Server
ADD https://cdn.sema4.ai/action-server/releases/2.13.1/linux64/action-server /usr/local/bin/action-server
RUN chmod +x /usr/local/bin/action-server

# Copy files first while still root
COPY . .

# Set correct ownership and permissions for SSH key

#COPY combined-tls.crt /action-server/actions/combined-tls.crt
#COPY tls.key /action-server/actions/tls.key
#RUN chown as-user:as-user /action-server/actions/combined-tls.crt /action-server/actions/tls.key && \
#    chmod 600 /action-server/actions/combined-tls.crt /action-server/actions/tls.key


USER as-user

RUN action-server import --datadir=/action-server/datadir

EXPOSE 8080

CMD ["/usr/bin/supervisord"]