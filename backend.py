from flask import Flask, jsonify, request
import psycopg2
import os
import sys
import time
import traceback

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://app_user:app_password@database:5432/app_db')

def get_db_connection():
    """Get a database connection"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route('/')
def home():
    return jsonify({
        'message': 'Backend API is running',
        'endpoints': {
            '/health': 'Health check',
            '/users': 'Get all users',
            '/users/<id>': 'Get user by ID',
            '/crash': 'Endpoint that causes a crash (DANGEROUS!)'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/users', methods=['GET', 'POST'])
def users():
    """Get all users or create a new user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            data = request.json
            name = data.get('name')
            email = data.get('email')
            
            cursor.execute(
                'INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email',
                (name, email)
            )
            user = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'id': user[0],
                'name': user[1],
                'email': user[2]
            }), 201
        
        # GET request
        cursor.execute('SELECT id, name, email FROM users')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify([
            {'id': user[0], 'name': user[1], 'email': user[2]}
            for user in users
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>')
def get_user(user_id):
    """Get a specific user by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({
                'id': user[0],
                'name': user[1],
                'email': user[2]
            })
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/crash')
def crash_endpoint():
    """
    INTENTIONAL BUG: divides by the caller's value. With value=0 (or missing)
    that raises ZeroDivisionError.

    Flask would normally turn an unhandled exception into a 500 response and
    keep serving, so a monitor watching the *container* would never notice.
    This service is deliberately less forgiving: it logs the traceback the way
    a real process would and exits, so the container leaves `running` and an
    agent has something genuine to detect, diagnose and restart.
    """
    data = request.args.get('value', '0')

    try:
        # INTENTIONAL BUG: no validation — value=0 divides by zero.
        result = 100 / int(data)
    except Exception:
        print("FATAL: unhandled exception in /crash — exiting", file=sys.stderr)
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        # os._exit skips Flask's error handling and atexit hooks: this process
        # is gone, exit code 1, and the container with it.
        os._exit(1)

    return jsonify({
        'result': result,
        'message': 'Calculation successful'
    })

@app.route('/dangerous-query')
def dangerous_query():
    """
    INTENTIONAL BUG: SQL injection vulnerability and potential crash
    """
    user_input = request.args.get('search', '')
    
    # INTENTIONAL BUG: Vulnerable to SQL injection and will crash on malformed input
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Unsafe query - directly concatenating user input
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    cursor.execute(query)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({'results': results})

def init_db():
    """Initialize the database with a users table"""
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL
                )
            ''')
            
            # Insert some sample data
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            
            if count == 0:
                sample_users = [
                    ('Alice Johnson', 'alice@example.com'),
                    ('Bob Smith', 'bob@example.com'),
                    ('Charlie Brown', 'charlie@example.com'),
                ]
                
                for name, email in sample_users:
                    cursor.execute(
                        'INSERT INTO users (name, email) VALUES (%s, %s)',
                        (name, email)
                    )
            
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully")
            break
        except Exception as e:
            retry_count += 1
            print(f"Failed to initialize database (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(2)

if __name__ == '__main__':
    print("Starting backend service...")
    init_db()
    # Debug only when asked (FLASK_DEBUG=1), and never the reloader: it forks a
    # child and would quietly resurrect the process after /crash exits, which
    # is exactly the failure this demo exists to show.
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug, use_reloader=False)
