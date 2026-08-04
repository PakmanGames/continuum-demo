# Multi-Service Demo Application

This is a demo application with multiple Docker containers showcasing a frontend, backend API, and PostgreSQL database.

## Architecture

- **Frontend**: a small Flask server that serves the page and proxies `/api/*` to the backend
- **Backend**: Flask API with intentional bugs for testing
- **Database**: PostgreSQL for data persistence

## Services

### Frontend (Port 3000)
A web interface that interacts with the backend API. It proxies `/api/*` to the
backend inside the compose network, so the page works on whichever port you publish it.

### Backend (Port 5000)
Flask REST API with the following endpoints:
- `GET /` - API information
- `GET /health` - Health check
- `GET /users` - Get all users
- `POST /users` - Create a new user
- `GET /users/<id>` - Get a specific user
- `GET /crash` - **DANGER**: Contains a division by zero bug
- `GET /dangerous-query` - **DANGER**: SQL injection vulnerability

### Database (Port 5432)
PostgreSQL database with user data.

## Running the Application

```bash
# Start all services
docker compose up --build

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Check running containers
docker ps
```

## Testing the Crash

The `/crash` endpoint contains an intentional bug — a division by the caller's
value — and, unlike a stock Flask app, it does not hide it behind a 500: it prints
the traceback and **exits with code 1**, so the container stops. With this
compose file (`restart: unless-stopped`) Docker brings it straight back; under the
Continuum agent's compose (`restart: "no"`) it stays down until the agent restarts it,
which is the point.

```bash
# This crashes the backend (division by zero) — the container exits
curl "http://localhost:5000/crash?value=0"

# This works normally
curl "http://localhost:5000/crash?value=5"
```

You can also trigger it from the web interface at http://localhost:3000 with the
**Trigger Crash** button. (Under the Continuum agent's compose the ports are 5001 and
3001.)

## Accessing Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Database**: localhost:5432

## Database Credentials

- Database: `app_db`
- User: `app_user`
- Password: `app_password`

## Intentional Bugs

1. **Division by Zero** (`/crash` endpoint): when `value=0` or not provided, a ZeroDivisionError is raised, logged, and the process exits
2. **SQL Injection** (`/dangerous-query` endpoint): vulnerable to SQL injection attacks
