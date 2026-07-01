# 🌐 Option 8 Setup Guide: Secure Nginx Proxy (HTTP/2 Multiplexing)

This guide provides step-by-step instructions for deploying a secure Nginx reverse proxy with HTTP/2 enabled in your ISF-Core environment.

## Why Upgrade to an Nginx HTTP/2 Proxy?
* **Bypass the 6-Connection Limit:** Modern browsers strictly limit HTTP/1.1 connections to a maximum of 6 concurrent streams per domain. If you are running multiple AI generation chats, workflows, or real-time data streams simultaneously, requests will stall in a `Pending` state.
* **HTTP/2 Multiplexing:** HTTP/2 allows dozens of concurrent streams (like Server-Sent Events for AI generation) to run simultaneously over a single TCP connection, entirely eliminating the browser-side bottleneck.
* **Security Context:** Browsers require HTTPS to enable HTTP/2. This setup includes self-signed SSL certificates to provide an encrypted HTTPS context locally or in private environments.
* **Native Load Balancing:** By combining Nginx with Docker's internal DNS, you can easily load-balance traffic across multiple `isf-core` backend replicas for horizontal scaling.

---

## Step 1: Directory & Certificate Setup

Because modern browsers require HTTPS to utilize HTTP/2, you must generate a self-signed certificate for your Nginx proxy.

1. **Create the Nginx directory structure:**
   ```bash
   mkdir -p nginx/ssl
   ```

2. **Generate a Self-Signed Certificate:**
   Run the following OpenSSL command to generate a certificate and private key.
   *(Note: Browsers will show a security warning for self-signed certificates. You can safely click "Proceed" or "Accept the risk" for local/internal deployments).*
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/nginx.key \
     -out nginx/ssl/nginx.crt \
     -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
   ```

---

## Step 2: Nginx Configuration

Create the Nginx template file that defines the proxy routing, HTTP/2 enforcement, and dynamic DNS resolution.

Create `nginx/nginx.conf.tpl`:
```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    # Resolve Docker internal DNS for dynamic upstream mapping
    resolver 127.0.0.11 valid=5s;

    server {
        # Listen on 443 with SSL and HTTP/2 enabled
        listen 443 ssl http2;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/nginx.crt;
        ssl_certificate_key /etc/nginx/ssl/nginx.key;

        # Route all API traffic to the FastAPI backend
        location /api/ {
            set $backend http://${ISF_BACKEND}:${ISF_BACKEND_PORT};
            proxy_pass $backend;

            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_addrs;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Disable buffering for Server-Sent Events (AI Streaming)
            proxy_buffering off;
            proxy_cache off;
            chunked_transfer_encoding on;
            proxy_read_timeout 86400;
        }

        # Route all other traffic to the Frontend
        location / {
            set $frontend http://${ISF_FRONTEND}:${ISF_FRONTEND_PORT};
            proxy_pass $frontend;

            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_addrs;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Websocket support (if needed for frontend HMR)
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

---

## Step 3: Docker Compose Deployment

Create a `compose.nginx.yml` file in the root of your project to launch the proxy.

Create `compose.nginx.yml`:
```yaml
services:
  nginx:
    image: nginx:alpine
    container_name: isf-nginx-proxy
    ports:
      - "443:443"
    volumes:
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/nginx.conf.tpl:/etc/nginx/nginx.conf.template:ro
    environment:
      - ISF_BACKEND=${ISF_BACKEND:-isf-core}
      - ISF_BACKEND_PORT=${ISF_BACKEND_PORT:-8002}
      - ISF_FRONTEND=${ISF_FRONTEND:-isf-core}
      - ISF_FRONTEND_PORT=${ISF_FRONTEND_PORT:-8002}
    command: /bin/sh -c "envsubst '\\$$ISF_BACKEND \\$$ISF_BACKEND_PORT \\$$ISF_FRONTEND \\$$ISF_FRONTEND_PORT' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"
    networks:
      - isf-network

networks:
  isf-network:
    external: true
```

---

## Step 4: Running the Setup

1. **Ensure your `isf-core` stack is running on the `isf-network`.**
2. **Start the Nginx proxy:**
   ```bash
   docker compose -f compose.nginx.yml up -d
   ```

You can now access your ISF-Core instance at **`https://localhost`** (or your machine's IP address). All API requests and concurrent streams will now utilize HTTP/2 Multiplexing, allowing virtually unlimited simultaneous connections!

---

## 🚀 Advanced: Scaling `isf-core` Replicas

Because the Nginx configuration uses dynamic Docker DNS resolution (`resolver 127.0.0.11`), you can easily scale your `isf-core` backend to distribute heavy workloads.

1. Scale the backend to 3 replicas:
   ```bash
   docker compose up -d --scale isf-core=3
   ```
2. Restart the Nginx proxy.

**Result:** The browser maintains a **single** HTTP/2 connection to Nginx, bypassing the 6-connection client limit. Nginx then automatically load-balances the requests round-robin across all 3 `isf-core` containers, solving the backend CPU/thread bottleneck as well.
