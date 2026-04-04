---
name: docker-nas
description: Manage Docker containers on a Synology NAS via SSH context. Use when asked to list, restart, stop, start, or inspect containers on the NAS, or when asked about NAS Docker management.
---

# Docker NAS Manager

Control Docker containers on the Synology NAS remotely using Docker SSH contexts.

## Network Configuration

- **NAS IP**: `192.168.2.44`
- **SSH Port**: `55522`
- **SSH User**: `nicolas`
- **Docker Context Name**: `nas`

## Prerequisites

These must be set up on the NAS (one-time setup):

```bash
# 1. SSH key copied to NAS
ssh-copy-id -p 55522 nicolas@192.168.2.44

# 2. User added to docker group on NAS
sudo synogroup --add docker nicolas

# 3. Symbolic link for docker binary (Synology PATH issue)
sudo ln -sf /usr/local/bin/docker /usr/bin/docker

# 4. Fix socket permissions (may reset after NAS reboot)
sudo chgrp docker /var/run/docker.sock
```

## Docker Context Setup

```bash
# Create the NAS context
docker context create nas --docker "host=ssh://nicolas@192.168.2.44:55522"

# Verify it was created
docker context ls
```

## Usage

### List containers on NAS

```bash
docker --context nas ps -a
```

### Restart a container

```bash
docker --context nas restart <container_name_or_id>
```

### Stop a container

```bash
docker --context nas stop <container_name_or_id>
```

### Start a container

```bash
docker --context nas start <container_name_or_id>
```

### View container logs

```bash
docker --context nas logs <container_name_or_id>
docker --context nas logs --tail 100 <container_name_or_id>
docker --context nas logs -f <container_name_or_id>  # follow mode
```

### Inspect a container

```bash
docker --context nas inspect <container_name_or_id>
```

### View container stats (CPU, memory, etc.)

```bash
docker --context nas stats
```

### Execute command in running container

```bash
docker --context nas exec -it <container_name_or_id> /bin/sh
```

### List images on NAS

```bash
docker --context nas images
```

### List volumes

```bash
docker --context nas volume ls
```

### List networks

```bash
docker --context nas network ls
```

## Troubleshooting

### Permission denied on /var/run/docker.sock

The socket permissions reset after NAS reboot. Fix from tmux root session:

```bash
chgrp docker /var/run/docker.sock
```

### SSH connection refused

- Verify SSH is enabled on NAS (Control Panel > Terminal & SNMP > Enable SSH)
- Check port 55522 is correct: `ssh -p 55522 nicolas@192.168.2.44`

### docker: command not found on remote

The symbolic link may be missing:

```bash
ssh -p 55522 nicolas@192.168.2.44 "sudo ln -sf /usr/local/bin/docker /usr/bin/docker"
```

## Switching Contexts

```bash
# Switch default context to NAS (optional, not recommended)
docker context use nas

# Revert to local Docker
docker context use default

# Or always use --context flag (recommended)
docker --context nas <command>
```
