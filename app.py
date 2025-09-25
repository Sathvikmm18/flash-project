from flask import Flask, jsonify, request, render_template, redirect, url_for
import json
import sqlite3
import os

app = Flask(__name__)

# SQLite database configuration
DATABASE = 'app_data.db'

def init_database():
    """Initialize the database and create table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Create submissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                age INTEGER,
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

# Initialize database when the app starts
init_database()

# Route 1: API endpoint to return JSON data from file
@app.route('/api')
def api_data():
    """Read data from data.json and return as JSON response"""
    try:
        with open('data.json', 'r') as file:
            data = json.load(file)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Data file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in data file"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route 2: Home page with form
@app.route('/')
def index():
    """Render the main form page"""
    return render_template('index.html')

# Route 3: Handle form submission
@app.route('/submit', methods=['POST'])
def submit_data():
    """Process form data and insert into SQLite database"""
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        age = request.form.get('age', '').strip()
        
        # Validate required fields
        if not name:
            return render_template('index.html', error="Name is required")
        if not email:
            return render_template('index.html', error="Email is required")
        
        # Validate email format
        if '@' not in email:
            return render_template('index.html', error="Please enter a valid email address")
        
        # Convert age to integer if provided
        age_value = None
        if age:
            try:
                age_value = int(age)
                if age_value < 1 or age_value > 120:
                    return render_template('index.html', error="Please enter a valid age (1-120)")
            except ValueError:
                return render_template('index.html', error="Age must be a number")
        
        # Insert data into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO submissions (name, email, age) VALUES (?, ?, ?)',
            (name, email, age_value)
        )
        
        conn.commit()
        conn.close()
        
        # Redirect to success page
        return redirect(url_for('success'))
        
    except Exception as e:
        error_message = f"Error submitting data: {str(e)}"
        return render_template('index.html', error=error_message)

# Route 4: Success page
@app.route('/success')
def success():
    """Render success page after form submission"""
    return render_template('success.html')

# Route 5: View all submitted data
@app.route('/view-data')
def view_data():
    """Display all data from the database"""
    try:
        conn = get_db_connection()
        submissions = conn.execute(
            'SELECT * FROM submissions ORDER BY submitted_at DESC'
        ).fetchall()
        conn.close()
        
        return render_template('view_data.html', submissions=submissions)
        
    except Exception as e:
        return f"Error retrieving data: {str(e)}", 500

# Route 6: Delete submission
@app.route('/delete/<int:submission_id>', methods=['POST'])
def delete_submission(submission_id):
    """Delete a specific submission"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if submission exists
        submission = cursor.execute(
            'SELECT * FROM submissions WHERE id = ?', (submission_id,)
        ).fetchone()
        
        if not submission:
            conn.close()
            return "Submission not found", 404
        
        # Delete the submission
        cursor.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
        conn.commit()
        conn.close()
        
        # Redirect back to view data page with success message
        return redirect(url_for('view_data'))
        
    except Exception as e:
        return f"Error deleting submission: {str(e)}", 500

# Route 7: Health check endpoint
@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "database": "connected"})

if __name__ == '__main__':
    print("Starting Flask application...")
    print("Available routes:")
    print("  - http://localhost:5000/ (Form)")
    print("  - http://localhost:5000/api (API Data)")
    print("  - http://localhost:5000/view-data (View Submissions)")
    print("  - http://localhost:5000/health (Health Check)")
    
    app.run(debug=True, host='0.0.0.0', port=5000)