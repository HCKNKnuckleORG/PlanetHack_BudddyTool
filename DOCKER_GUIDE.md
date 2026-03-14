# Docker Guide - PlanetHack

Guide for running PlanetHack in Docker on Linux.

**Note:** For full recon workflow (GUI + Kali tools), run natively on Kali: `python main.py --gui`. Docker is for headless/CLI use when a display is unavailable.

## Prerequisites

1. **Docker** and **Docker Compose** installed

2. **Verify Docker is working**
   ```bash
   docker --version
   docker-compose --version
   ```

## Quick Start (Docker Compose - Recommended)

### Step 1: Navigate to Project Directory

```bash
cd PlanetHack_BudddyTool
```

### Step 2: Build and Start Containers

```bash
docker-compose up -d
```

This will:
- Build the PlanetHack Docker image
- Start the container in detached mode
- Create necessary volumes for logs and config

### Step 3: View Logs

```bash
docker-compose logs -f
```

### Step 4: Access the Application

Since the GUI requires a display, you have two options:

**Option A: Execute commands inside container**
```bash
docker-compose exec planet-hack python main.py --cli
```

**Option B: Run interactive shell**
```bash
docker-compose exec planet-hack bash
# Then inside container:
python main.py --cli
```

### Step 5: Stop Containers

```bash
docker-compose down
```

---

## Running with Ollama (AI-assisted next steps)

To run PlanetHack with Ollama for AI-assisted next steps:

**Option A: Python locally (Ollama + Web UI)**
```bash
./launch_web_with_ollama.sh
```
Or use the unified launcher: `./launch.sh` → option 6.

**Option B: Docker (PlanetHack + Ollama containers)**
```bash
docker-compose -f docker-compose.yml -f docker-compose.ollama.yml --profile ollama up -d
```
Or use `./launch.sh` → option 7.

Then pull a model:
```bash
docker exec planet-hack-ollama ollama pull llama3
```

- Web UI: http://localhost:8080
- Ollama API: http://localhost:11434

To also remove volumes:
```bash
docker-compose down -v
```

---

## Manual Docker Build (Alternative)

### Step 1: Build the Image

```bash
cd PlanetHack_BudddyTool
docker build -t planethack/ctf-tool:latest .
```

### Step 2: Run the Container

**For CLI mode:**
```bash
docker run -it --rm \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/config:/app/config" \
  planethack/ctf-tool:latest python main.py --cli
```

**For interactive shell:**
```bash
docker run -it --rm \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/config:/app/config" \
  planethack/ctf-tool:latest bash
```

---

## Common Commands

### View Running Containers
```bash
docker-compose ps
```

### View Container Logs
```bash
docker-compose logs planet-hack
docker-compose logs -f planet-hack  # Follow logs
```

### Execute Command in Container
```bash
docker-compose exec planet-hack python main.py --module recon --target https://example.com
```

### Rebuild After Changes
```bash
docker-compose build --no-cache
docker-compose up -d
```

### View Container Resource Usage
```bash
docker stats planet-hack-ctf
```

### Remove Everything and Start Fresh
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

---

## Troubleshooting

### Issue: "Cannot connect to Docker daemon"
**Solution**: Ensure Docker daemon is running (`sudo systemctl start docker`)

### Issue: "Port already in use"
**Solution**: Change port in `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # Change 8080 to 8081
```

### Issue: "Permission denied" on volumes
**Solution**: Ensure your user is in the `docker` group: `sudo usermod -aG docker $USER`

### Issue: GUI doesn't work in container
**Solution**: 
- GUI requires X11 forwarding
- Use CLI mode instead: `python main.py --cli`
- Or use VNC/X11 server for GUI access

### Issue: Container exits immediately
**Solution**: 
- Check logs: `docker-compose logs planet-hack`
- Run in interactive mode: `docker-compose run --rm planet-hack bash`

### Issue: Module import errors
**Solution**: 
- Rebuild image: `docker-compose build --no-cache`
- Check requirements.txt is correct

---

## Advanced: Using with Database

The `docker-compose.yml` includes an optional PostgreSQL database. **Change the default password** by setting `POSTGRES_PASSWORD` in a `.env` file (copy from `.env.example`):

```bash
# Start with database
docker-compose --profile with-db up -d
```

Access database:
```bash
docker-compose exec postgres psql -U planethack -d planethack
```

---

## Environment Variables

Set environment variables in `docker-compose.yml`:

```yaml
environment:
  - ENV=prod
  - LOG_LEVEL=DEBUG
```

Or pass when running:
```bash
docker run -e ENV=prod -e LOG_LEVEL=DEBUG planethack/ctf-tool:latest
```

---

## Volume Mounts Explained

The docker-compose.yml mounts:
- `./logs:/app/logs` - Application logs persist on host
- `./config:/app/config` - Configuration files
- `./python:/app/python` - Python code (for development)

**Note**: Mounting `./python` allows code changes without rebuilding image (development mode).

---

## Production Deployment

For production, don't mount the `python` directory:

```yaml
volumes:
  - ./logs:/app/logs
  - ./config:/app/config
  # Remove: - ./python:/app/python
```

This ensures you're running the code baked into the image.

---

## Next Steps

1. **Test the installation:**
   ```bash
   docker-compose exec planet-hack python main.py --cli
   ```

2. **Run a module:**
   ```bash
   docker-compose exec planet-hack python main.py --module recon --target http://testphp.vulnweb.com
   ```

3. **Check logs:**
   ```bash
   docker-compose logs -f planet-hack
   ```

---

**Remember: Only hack systems you own or have explicit permission to test!**

