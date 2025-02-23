FROM postgres:15

# Install required packages
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Patroni with PostgreSQL dependencies
RUN pip3 install --no-cache-dir --break-system-packages \
    patroni[postgresql] \
    psycopg2-binary \
    python-etcd

# Create required directories
RUN mkdir -p /data/patroni /etc/patroni

# Copy configuration files
COPY patroni.yml /etc/patroni/
COPY entrypoint.sh /

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
