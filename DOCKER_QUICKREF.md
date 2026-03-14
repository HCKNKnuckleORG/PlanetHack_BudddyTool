# Docker Quick Reference Card

## 🚀 Most Common Commands

### Start Everything
```bash
docker-compose up -d
```

### Run CLI
```bash
docker-compose exec planet-hack python main.py --cli
```

### View Logs
```bash
docker-compose logs -f planet-hack
```

### Stop Everything
```bash
docker-compose down
```

### Interactive Shell
```bash
docker-compose exec planet-hack bash
```

---

## 📋 Complete Command List

| Task | Command |
|------|---------|
| **Build & Start** | `docker-compose up -d --build` |
| **Start** | `docker-compose up -d` |
| **Stop** | `docker-compose down` |
| **Stop + Remove Volumes** | `docker-compose down -v` |
| **View Logs** | `docker-compose logs -f` |
| **View Logs (last 100 lines)** | `docker-compose logs --tail=100` |
| **Run CLI** | `docker-compose exec planet-hack python main.py --cli` |
| **Run Module** | `docker-compose exec planet-hack python main.py --module recon --target https://example.com` |
| **Interactive Shell** | `docker-compose exec planet-hack bash` |
| **Rebuild** | `docker-compose build --no-cache` |
| **View Status** | `docker-compose ps` |
| **View Resource Usage** | `docker stats planet-hack-ctf` |
| **Remove Everything** | `docker-compose down -v` then rebuild |

---

## ⚡ One-Liners

**Quick test:**
```bash
docker-compose up -d && docker-compose exec planet-hack python main.py --cli
```

**Fresh start:**
```bash
docker-compose down -v && docker-compose build --no-cache && docker-compose up -d
```

**Check if running:**
```bash
docker-compose ps
```

---

## 🔧 Troubleshooting

**Docker not running?**
- `sudo systemctl start docker`

**Port in use?**
- Edit `docker-compose.yml`, change `8080:8080` to `8081:8080`

**Need to rebuild?**
```bash
docker-compose build --no-cache
docker-compose up -d
```

---

**Full guide:** See [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
