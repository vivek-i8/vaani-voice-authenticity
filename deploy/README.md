# VAANI V2 Deployment

## Oracle Always Free Ampere A1

### Prerequisites
- Oracle Always Free Ampere A1 VM (4 OCPU / 24 GB RAM)
- Docker and Docker Compose installed
- Ports 8000 (backend) and 443 (HTTPS) open

### Deploy
```bash
cd deploy
docker-compose up -d
```

### Verify
```bash
curl http://localhost:8000/api/health
```

### Frontend (Cloudflare Pages)
1. Build frontend: `cd frontend && npm run build`
2. Deploy `frontend/dist/public/` to Cloudflare Pages
3. Set `VITE_API_BASE_URL` to your backend URL

### Memory Budget
- Wav2Vec2 XLS-R-53: ~1.2GB
- Fusion Head: ~5MB
- Spectra-AASIST3: ~1.38GB
- Total: ~2.6GB (fits in 24GB RAM)
