# Infrastructure Notes

- Frontend is designed for Vercel deployment.
- Backend is designed for Render / Railway / AWS container deployment.
- `docker-compose.yml` at the repository root provides local PostgreSQL + Redis services for development.
- Production DNS can use a dedicated API subdomain, e.g. `api.thorpeworkforce.ai`, with frontend configured via `NEXT_PUBLIC_API_BASE_URL`.
- Railway-specific setup is documented in `infrastructure/railway.md`.
