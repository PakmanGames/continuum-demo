# Multi-Service Demo Application

This is a demo application with multiple Docker containers showcasing a frontend, backend API, and PostgreSQL database.

## Architecture

- **Frontend**: Nginx serving a simple web interface
- **Backend**: Flask API with intentional bugs for testing
- **Database**: PostgreSQL for data persistence

## Services

### Frontend (Port 3000)
A web interface that interacts with the backend API.

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

The `/crash` endpoint contains an intentional bug that will crash the backend:

```bash
# This will crash the backend (division by zero)
curl http://localhost:5000/crash?value=0

# This will work normally
curl http://localhost:5000/crash?value=5
```

You can also trigger the crash from the web interface at http://localhost:3000

## Accessing Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Database**: localhost:5432

## Database Credentials

- Database: `app_db`
- User: `app_user`
- Password: `app_password`

## Intentional Bugs

1. **Division by Zero** (`/crash` endpoint): When `value=0` or not provided, causes ZeroDivisionError
2. **SQL Injection** (`/dangerous-query` endpoint): Vulnerable to SQL injection attacks

The application intentionally tries to connect to a non-existent database host (`nonexistent-database-host`) to simulate connection failures. This is useful for testing error handling, monitoring, and logging systems.
