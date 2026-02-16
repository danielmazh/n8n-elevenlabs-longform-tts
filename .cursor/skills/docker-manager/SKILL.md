---
name: docker-manager
description: Manage Docker containers, images, and docker-compose services via terminal commands. Use when the user asks about container state, service health, building images, starting/stopping services, viewing logs, or any docker/docker-compose operation.
---

# Docker Manager

## Role

Docker Infrastructure Automation agent. Executes `docker` and `docker-compose` CLI commands to manage containers, images, networks, volumes, and multi-container orchestration.

## Core Rules

### 1. Safety-First Execution

**Destructive or state-changing commands require explicit approval.** Before running any of the following, summarize the plan and wait for the user's "OK":

- `docker-compose up / down / build / restart`
- `docker stop / rm / kill`
- `docker rmi / image prune / system prune`
- `docker volume rm / network rm`

**Read-only commands run immediately** without asking:

- `docker ps -a`, `docker images`, `docker logs`
- `docker-compose ps`, `docker-compose logs`
- `docker inspect`, `docker stats`, `docker network ls`
- `docker volume ls`, `docker top`

### 2. Credential Handling

**Never store or echo credentials, tokens, or passwords in any file.**

- Docker Hub authentication is handled via `docker login` run manually by the user.
- The agent inherits the authenticated session from the terminal.
- If a command fails with an auth error, prompt the user to run `docker login` manually.
- Never reference or log access tokens, even partially.

### 3. Service State Checks

When the user asks about service state:

1. Run `docker-compose ps` if a `docker-compose.yml` exists in the project.
2. Otherwise run `docker ps -a` for a full container listing.
3. Present results in a concise summary: name, status, ports, health.

### 4. Log Inspection

When asked to check logs:

```bash
# Last 100 lines with timestamps
docker-compose logs --tail=100 -t <service>

# Follow logs (background immediately)
docker-compose logs -f <service>
```

For single containers: `docker logs --tail=100 -t <container>`

### 5. Health Monitoring

When checking health:

1. `docker ps` — look at STATUS column for health indicators.
2. `docker inspect --format='{{json .State.Health}}' <container>` — for detailed health check output.
3. `docker stats --no-stream` — for CPU/memory snapshot.

## Common Workflows

### Start Services

```
Plan summary:
1. Build images (if --build requested)
2. Start containers in detached mode
3. Verify all services are healthy

Command: docker-compose up -d [--build]
```

**Always wait for user "OK" before executing.**

### Stop Services

```
Plan summary:
1. Gracefully stop all services
2. Remove containers and default network

Command: docker-compose down [-v to also remove volumes]
```

**Always wait for user "OK" before executing.**

### Rebuild a Single Service

```
Plan summary:
1. Stop the target service
2. Rebuild its image (no cache if requested)
3. Restart the service

Commands:
  docker-compose stop <service>
  docker-compose build [--no-cache] <service>
  docker-compose up -d <service>
```

**Always wait for user "OK" before executing.**

### Cleanup

```
Plan summary:
1. Remove stopped containers
2. Remove dangling images
3. Optionally prune volumes

Commands:
  docker system prune -f
  docker volume prune -f  (only if requested)
```

**Always wait for user "OK" before executing.**

## Troubleshooting

| Symptom | Diagnostic Command | Next Step |
|---------|-------------------|-----------|
| Container restarting | `docker logs --tail=50 <ctr>` | Check exit code and error output |
| Port conflict | `docker ps --format 'table {{.Names}}\t{{.Ports}}'` | Identify conflicting port mappings |
| Image build fails | `docker-compose build --no-cache <svc>` | Rebuild without layer cache |
| Out of disk space | `docker system df` | Suggest `docker system prune` |
| Auth error on pull | — | Ask user to run `docker login` manually |
| Network unreachable | `docker network ls && docker network inspect <net>` | Check network config |
