# bind9

A simple, container-friendly setup for running a BIND 9 DNS server using Docker Compose.

## Overview

This project provides a straightforward way to deploy a BIND 9 DNS server using Docker. It leverages best practices for maintainability and portability, mapping local configuration files into the container and exposing required ports for DNS functionality.

## Features

- **Docker Compose integration** for easy setup and management
- **Custom configuration support**: Easily mount your own `named.conf`, zone files, and other config
- **Volume mapping** for persistent and customizable DNS records
- **Support for both TCP and UDP port 53**
- Ideal for homelab, dev, and small production environments

## Directory Structure

```
bind9/
├── compose.yaml
├── config/
│ ├── named.conf
│ └── <other config/zone files>
├── .env.eg
├── .gitignor
├── LICENSE
```

- **compose.yaml**: Main Docker Compose file that defines the service.
- **config/**: Store your BIND configuration and zone files here.
- **.env.eg**: Example environment configuration.

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Setup Instructions

1. **Clone This Repository**

```
git clone https://github.com/kdpuvvadi/bind9.git
cd bind9
```

2. **Configure DNS**

Place your BIND config files and zones in the `config/` directory. Files might include:
- `named.conf`
- Zone files (e.g., `db.example.com`)

3. **(Optional) Customize Environment Variables**

Copy `.env.eg` to `.env` and edit as needed for your environment.

4. **Launch the DNS Server**

```
docker compose up -d
```

5. **Check the Service**

Make sure the DNS server is running:

```
docker compose ps
```

Test DNS resolution using `dig` or `nslookup` from another machine, targeting your server's IP.

## Example `compose.yaml`

A typical Compose file for BIND 9 might look like:

```
---
services:
  bind9:
    container_name: dns
    image: ubuntu/bind9:latest
    env_file:
      - .env
    volumes:
      - ./config:/etc/bind:rw
      - ./cache:/var/cache/bind:rw
      - ./records:/var/lib/bind:rw
      - ./logs:/var/log/bind:rw
    user: root
    ports:
      - 53:53/tcp
      - 53:53/udp
    restart: always
```

## Configuration Notes

- **Zone files and configuration**: Place all your custom configuration in the `config/` directory.
- **Persistence**: All config changes are persistent as they are mapped from your host.
- **Security**: Review and restrict access to the DNS server ports as appropriate for your environment.

## Useful Commands

- **View logs:**

```
docker compose logs bind9
```

- **Reload BIND configuration after changes:**

```
docker compose restart bind9
```

## References

- [Official ubuntu/bind9 image](https://hub.docker.com/r/ubuntu/bind9)
- General guides to running BIND 9 with Docker Compose

## License

MIT(/LICENSE)
