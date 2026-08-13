# Architecture overview

Ahara is a modular monolith. The Next.js web application calls the FastAPI health endpoint over HTTP. FastAPI owns connections to PostgreSQL and Redis, which are Docker services during development.

No product domain, external API, or AI integration is present in this foundation.
