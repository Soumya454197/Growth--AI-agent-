from flask import Flask, request, jsonify, send_from_directory, session, Response, redirect, url_for
from flask_cors import CORS
import requests
import json
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import PyPDF2
import pdfplumber
from typing import List
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

# Import database functions
try:
    from database import (
        init_database, create_user_in_db, get_user_from_db,
        update_user_chat_history, save_uploaded_file_to_db,
        get_user_files_from_db
    )
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Database module not available: {e}")
    print("📁 Falling back to file-based storage")
    DATABASE_AVAILABLE = False

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='.')
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Configure session management
app.secret_key = secrets.token_hex(16)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Store uploaded files and their analysis (per user)
uploaded_files = {}

# File-based user storage (persistent across server restarts)
users_db = {}
user_sessions = {}

def ensure_users_directory():
    """Create users directory if it doesn't exist"""
    users_dir = 'users'
    if not os.path.exists(users_dir):
        os.makedirs(users_dir)
        print(f"✅ Created users directory: {users_dir}")
    return users_dir

def save_user_to_file(user_id, user_data):
    """Save individual user data to file"""
    users_dir = ensure_users_directory()
    user_file = os.path.join(users_dir, f"{user_id}.json")

    try:
        with open(user_file, 'w') as f:
            json.dump(user_data, f, indent=2)
        print(f"✅ User saved to file: {user_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving user to file: {e}")
        return False

def load_user_from_file(user_id):
    """Load individual user data from file"""
    users_dir = ensure_users_directory()
    user_file = os.path.join(users_dir, f"{user_id}.json")

    try:
        if os.path.exists(user_file):
            with open(user_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ Error loading user from file: {e}")
    return None

def load_all_users():
    """Load all users from files into memory"""
    users_dir = ensure_users_directory()
    loaded_count = 0

    if os.path.exists(users_dir):
        for filename in os.listdir(users_dir):
            if filename.endswith('.json'):
                user_id = filename[:-5]  # Remove .json extension
                user_data = load_user_from_file(user_id)
                if user_data:
                    users_db[user_id] = user_data
                    uploaded_files[user_id] = {}  # Initialize file storage
                    loaded_count += 1

    print(f"✅ Loaded {loaded_count} users from files")
    return loaded_count

def create_test_user():
    """Create a test user for debugging"""
    test_user_id = "test_user_123"

    # Check if test user already exists in file
    existing_user = load_user_from_file(test_user_id)
    if existing_user:
        users_db[test_user_id] = existing_user
        uploaded_files[test_user_id] = {}
        print(f"✅ Test user loaded from file: testuser (test@example.com)")
        return

    # Create new test user
    test_user_data = {
        'id': test_user_id,
        'email': 'test@example.com',
        'username': 'testuser',
        'password_hash': generate_password_hash('TestPass123'),
        'created_at': datetime.now().isoformat(),
        'chat_history': {}
    }

    users_db[test_user_id] = test_user_data
    uploaded_files[test_user_id] = {}
    save_user_to_file(test_user_id, test_user_data)
    print(f"✅ Test user created and saved: testuser (test@example.com)")

# Initialize database or fallback to file storage
if DATABASE_AVAILABLE:
    print("🔄 Initializing PostgreSQL database...")
    if init_database():
        print("✅ Using PostgreSQL database")
        USE_DATABASE = True
    else:
        print("❌ PostgreSQL failed, falling back to file storage")
        USE_DATABASE = False
        load_all_users()
        create_test_user()
else:
    print("📁 Using file-based storage")
    USE_DATABASE = False
    load_all_users()
    create_test_user()

# Authentication helper functions
def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required", "redirect": "/login"}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current authenticated user"""
    user_id = session.get('user_id')
    if user_id and user_id in users_db:
        return users_db[user_id]
    return None

def create_user_session(user_id, remember_me=False):
    """Create a user session"""
    session['user_id'] = user_id
    session['login_time'] = datetime.now().isoformat()
    if remember_me:
        session.permanent = True

    # Store session info
    user_sessions[user_id] = {
        'login_time': datetime.now().isoformat(),
        'remember_me': remember_me
    }

def validate_user_input(data, required_fields):
    """Validate user input data"""
    errors = {}

    for field in required_fields:
        if field not in data or not data[field].strip():
            errors[field] = f"{field.capitalize()} is required"

    # Email validation
    if 'email' in data and data['email']:
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, data['email']):
            errors['email'] = "Invalid email format"

    # Username validation
    if 'username' in data and data['username']:
        if len(data['username']) < 3:
            errors['username'] = "Username must be at least 3 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', data['username']):
            errors['username'] = "Username can only contain letters, numbers, and underscores"

    # Password validation
    if 'password' in data and data['password']:
        password = data['password']
        if len(password) < 8:
            errors['password'] = "Password must be at least 8 characters"
        if not re.search(r'[a-z]', password):
            errors['password'] = "Password must contain lowercase letters"
        if not re.search(r'[A-Z]', password):
            errors['password'] = "Password must contain uppercase letters"
        if not re.search(r'\d', password):
            errors['password'] = "Password must contain numbers"

    return errors

class DocumentAnalyzer:
    def __init__(self):
        self.ollama_url = 'http://localhost:11434/api/chat'

    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF using multiple methods"""
        try:
            # Try pdfplumber first (better extraction)
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            if text.strip():
                return text.strip()

            # Fallback to PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"

            return text.strip()
        except Exception as e:
            return f"Error extracting text: {str(e)}"

    def extract_excel_text(self, excel_path: str) -> str:
        """Extract text from Excel files"""
        try:
            import pandas as pd

            # Read all sheets
            excel_file = pd.ExcelFile(excel_path)
            all_text = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)

                # Convert DataFrame to text
                sheet_text = f"Sheet: {sheet_name}\n"
                sheet_text += df.to_string(index=False, na_rep='')
                all_text.append(sheet_text)

            return "\n\n".join(all_text)

        except Exception as e:
            return f"Error extracting Excel data: {str(e)}"

    def chunk_text_for_tinyllama(self, text: str, max_chunk_size: int = 400) -> List[str]:
        """Split text into chunks suitable for TinyLlama"""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()

        # Split by sentences
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            test_chunk = current_chunk + " " + sentence + "."

            if len(test_chunk) <= max_chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "."

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def analyze_with_tinyllama(self, text_chunk: str) -> str:
        """Analyze text chunk with TinyLlama"""
        prompt = f"""
Please read this text and extract the most important points as bullet points:

Text: {text_chunk}

Key points:
•"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "tinyllama",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]

            return "Error: Could not analyze this section"
        except Exception as e:
            return f"Analysis error: {str(e)}"

    def create_summary(self, all_points: List[str]) -> str:
        """Create final summary from all points"""
        combined_points = "\n\n".join(all_points)

        prompt = f"""
Based on these key points from a document, create a brief summary:

{combined_points}

Summary:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "tinyllama",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]

            return "Could not create summary"
        except Exception as e:
            return f"Summary error: {str(e)}"

    def analyze_document_full(self, file_path: str) -> dict:
        """Complete document analysis for PDF or Excel files"""
        # Determine file type and extract text accordingly
        if file_path.lower().endswith('.pdf'):
            text = self.extract_pdf_text(file_path)
            doc_type = "PDF"
        elif file_path.lower().endswith(('.xlsx', '.xls')):
            text = self.extract_excel_text(file_path)
            doc_type = "Excel"
        else:
            return {
                "success": False,
                "error": "Unsupported file type"
            }

        if text.startswith("Error") or len(text) < 50:
            return {
                "success": False,
                "error": "Could not extract readable text from PDF"
            }

        # Split into chunks
        chunks = self.chunk_text_for_tinyllama(text)

        if not chunks:
            return {
                "success": False,
                "error": "No content to analyze"
            }

        # Analyze each chunk (limit to first 3 chunks for speed)
        all_points = []
        max_chunks = min(3, len(chunks))  # Process max 3 chunks for speed
        for i, chunk in enumerate(chunks[:max_chunks]):
            print(f"Analyzing chunk {i+1}/{max_chunks}...")
            points = self.analyze_with_tinyllama(chunk)
            if points and not points.startswith("Error"):
                all_points.append(f"Section {i+1}:\n{points}")

        # Create summary if multiple chunks
        if len(chunks) > 1 and all_points:
            summary = self.create_summary(all_points)
        else:
            summary = all_points[0] if all_points else "No analysis available"

        return {
            "success": True,
            "chunks_processed": len(chunks),
            "summary": summary,
            "detailed_points": all_points
        }

# Initialize document analyzer
document_analyzer = DocumentAnalyzer()

# Authentication Routes
@app.route('/login')
def login_page():
    """Serve the login page"""
    return send_from_directory('login_signup', 'login.html')

@app.route('/login.css')
def login_css():
    """Serve the login CSS"""
    return send_from_directory('login_signup', 'login.css')

@app.route('/login.js')
def login_js():
    """Serve the login JavaScript"""
    return send_from_directory('login_signup', 'login.js')

@app.route('/api/auth/signup', methods=['POST', 'OPTIONS'])
def signup():
    """Handle user registration"""
    print("=== SIGNUP ENDPOINT HIT ===")
    print(f"Request method: {request.method}")

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        print("Handling OPTIONS preflight request")
        return '', 200

    try:
        data = request.get_json()
        print(f"Signup attempt with data: {data}")  # Debug logging
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request content type: {request.content_type}")
        print(f"Raw request data: {request.data}")

        # Simple validation for signup
        if not data.get('email') or not data.get('username') or not data.get('password'):
            print("Signup failed: Missing required fields")
            return jsonify({"success": False, "message": "Please fill in all fields"}), 400

        # Basic email validation
        email = data['email'].strip().lower()
        if '@' not in email or '.' not in email:
            print("Signup failed: Invalid email format")
            return jsonify({"success": False, "message": "Please enter a valid email address"}), 400

        # Basic password validation
        password = data['password']
        if len(password) < 6:
            print("Signup failed: Password too short")
            return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400

        username = data['username'].strip()

        # Check if user already exists
        for user_id, user in users_db.items():
            if user['email'] == email:
                return jsonify({"success": False, "message": "Email already registered"}), 400
            if user['username'] == username:
                return jsonify({"success": False, "message": "Username already taken"}), 400

        # Create new user
        user_id = secrets.token_hex(16)

        if USE_DATABASE:
            # Save to PostgreSQL database
            success, message = create_user_in_db(user_id, email, username, password)
            if not success:
                return jsonify({"success": False, "message": message}), 400

            print(f"New user registered in PostgreSQL: {username} ({email}) with ID: {user_id}")
        else:
            # Fallback to file storage
            user_data = {
                'id': user_id,
                'email': email,
                'username': username,
                'password_hash': generate_password_hash(password),
                'created_at': datetime.now().isoformat(),
                'chat_history': {}
            }

            # Save to memory
            users_db[user_id] = user_data

            # Save to file (persistent storage)
            save_user_to_file(user_id, user_data)

            print(f"New user registered in files: {username} ({email}) with ID: {user_id}")

        # Initialize user's uploaded files storage
        uploaded_files[user_id] = {}

        return jsonify({
            "success": True,
            "message": "Account created successfully! You can now sign in.",
            "user": {
                "id": user_id,
                "username": username,
                "email": email
            }
        })

    except Exception as e:
        print(f"Signup error: {str(e)}")
        return jsonify({"success": False, "message": "Registration failed. Please try again."}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Handle user login"""
    print("=== LOGIN ENDPOINT HIT ===")
    print(f"Request method: {request.method}")

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        print("Handling OPTIONS preflight request")
        return '', 200

    try:
        data = request.get_json()
        print(f"Login attempt with data: {data}")  # Debug logging
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request content type: {request.content_type}")
        print(f"Raw request data: {request.data}")

        # Simple validation for login - just check if fields exist
        if not data or not data.get('email') or not data.get('password'):
            print("Login failed: Missing email or password fields")
            return jsonify({"success": False, "message": "Please fill in all fields"}), 400

        if not data['email'].strip() or not data['password'].strip():
            print("Login failed: Empty email or password")
            return jsonify({"success": False, "message": "Please fill in all fields"}), 400

        email_or_username = data['email'].strip().lower()
        password = data['password']
        remember_me = data.get('rememberMe', False)

        # Find user by email or username
        user = None
        user_id = None
        print(f"Looking for user with email/username: {email_or_username}")

        if USE_DATABASE:
            # Try to find user in PostgreSQL database
            user = get_user_from_db(email=email_or_username)
            if user:
                user_id = user['id']
                print(f"Found user in PostgreSQL: {user['username']}")
        else:
            # Fallback to file storage
            print(f"Current users in database: {list(users_db.keys())}")
            for uid, u in users_db.items():
                print(f"Checking user: {u['email']} / {u['username']}")
                if u['email'] == email_or_username or u['username'] == email_or_username:
                    user = u
                    user_id = uid
                    print(f"Found matching user: {u['username']}")
                    break

        if not user:
            print("No user found with that email/username")
            return jsonify({"success": False, "message": "Invalid email/username or password"}), 401

        if not check_password_hash(user['password_hash'], password):
            print("Password verification failed")
            return jsonify({"success": False, "message": "Invalid email/username or password"}), 401

        # Create session
        create_user_session(user_id, remember_me)

        print(f"User logged in: {user['username']}")

        return jsonify({
            "success": True,
            "message": "Login successful!",
            "user": {
                "id": user_id,
                "username": user['username'],
                "email": user['email']
            }
        })

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"success": False, "message": "Login failed. Please try again."}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    user_id = session.get('user_id')
    if user_id:
        # Remove from user sessions
        user_sessions.pop(user_id, None)
        # Clear session
        session.clear()
        print(f"User logged out: {user_id}")

    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    user = get_current_user()
    if user:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email']
            }
        })
    else:
        return jsonify({"authenticated": False}), 401

@app.route('/api/auth/auto-login', methods=['POST'])
def auto_login():
    """Auto-login for persistent sessions"""
    user = get_current_user()
    if user:
        return jsonify({
            "success": True,
            "message": "Auto-login successful",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email']
            }
        })
    else:
        return jsonify({"success": False, "message": "No active session"}), 401

@app.route('/api/debug/users', methods=['GET'])
def debug_users():
    """Debug endpoint to check users in database"""
    return jsonify({
        "total_users": len(users_db),
        "users": [
            {
                "id": user_id,
                "email": user['email'],
                "username": user['username']
            }
            for user_id, user in users_db.items()
        ]
    })

@app.route('/api/test', methods=['GET', 'POST'])
def test_endpoint():
    """Simple test endpoint to verify backend connectivity"""
    print("=== TEST ENDPOINT HIT ===")
    print(f"Method: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    if request.method == 'POST':
        data = request.get_json()
        print(f"POST data: {data}")
        return jsonify({"message": "POST received", "data": data})
    return jsonify({"message": "Backend is working!", "method": request.method})

@app.route('/api/test-login', methods=['POST'])
def test_login():
    """Test login endpoint to verify connection"""
    print("=== TEST LOGIN ENDPOINT HIT ===")
    try:
        data = request.get_json()
        print(f"Test login data: {data}")

        # Test with the known test user
        if data and data.get('email') == 'test@example.com' and data.get('password') == 'TestPass123':
            return jsonify({
                "success": True,
                "message": "Test login successful!",
                "user": {"username": "testuser", "email": "test@example.com", "id": "test_user_123"}
            })
        else:
            return jsonify({"success": False, "message": "Test login failed - use test@example.com / TestPass123"})
    except Exception as e:
        print(f"Test login error: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/')
def index():
    """Main route - serve chat interface (authentication is optional)"""
    return send_from_directory('static_', 'chat.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('static_', path)

def generate_fallback_response(user_message, user_id=None):
    """Generate contextual fallback responses when AI service is unavailable"""
    message = user_message.lower().strip()

    # Check if asking about uploaded files
    if any(word in message for word in ['analyze', 'pdf', 'excel', 'spreadsheet', 'document', 'file', 'uploaded', 'data']):
        # Check for files from authenticated user or guest users
        all_files = {}
        if user_id:
            all_files.update(uploaded_files.get(user_id, {}))

        # Also check guest files
        for uid, files in uploaded_files.items():
            if uid.startswith('guest_'):
                all_files.update(files)

        if all_files:
            file_list = ", ".join(all_files.keys())
            return f"I can see you have uploaded: {file_list}. However, I'm currently unable to analyze them because the AI service is unavailable. Please try again later."
        else:
            return "I don't see any uploaded files. Please upload a PDF first, then ask me to analyze it."

    # Python-related questions
    if 'python' in message:
        return "Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used for web development, data science, AI/ML, automation, and more. Python emphasizes code readability with its clean syntax and is great for beginners and experts alike."

    # Programming questions
    if any(word in message for word in ['programming', 'code', 'coding', 'software', 'development']):
        return "Programming is the process of creating instructions for computers to follow. It involves writing code in various languages like Python, JavaScript, Java, etc. Programming helps solve problems, automate tasks, and build applications that make our lives easier."

    # AI/ML questions
    if any(word in message for word in ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural network']):
        return "Artificial Intelligence (AI) is technology that enables machines to simulate human intelligence. Machine Learning is a subset of AI where systems learn from data to make predictions or decisions. It's used in everything from recommendation systems to autonomous vehicles."

    # Web development
    if any(word in message for word in ['web', 'website', 'html', 'css', 'javascript', 'frontend', 'backend']):
        return "Web development involves creating websites and web applications. Frontend development focuses on user interfaces (HTML, CSS, JavaScript), while backend development handles server-side logic and databases. Modern web development uses frameworks like React, Vue, Django, and Flask."

    # Greetings
    if any(word in message for word in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! I'm Growth, your AI assistant. While my main AI service is temporarily unavailable, I can still help with basic questions about programming, technology, and general topics. What would you like to know?"

    # Help requests
    if any(word in message for word in ['help', 'assist', 'support']):
        return "I'm here to help! Although my advanced AI capabilities are temporarily offline, I can provide information on programming, technology, and general topics. Feel free to ask about Python, web development, AI, or other tech subjects."

    # Default response
    return f"I understand you're asking about '{user_message}'. While my main AI service is temporarily unavailable, I'm still here to help with basic questions. Could you try rephrasing your question or ask about programming, technology, or general topics?"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    stream_response = data.get('stream', True)  # Default to streaming
    user_id = session.get('user_id')
    user = get_current_user()

    # Log message with user info if available
    if user:
        print(f"Received message from {user['username']}: {user_message} (stream: {stream_response})")
    else:
        print(f"Received message from guest: {user_message} (stream: {stream_response})")

    # Check if user is asking about document analysis (PDF or Excel)
    message_lower = user_message.lower()
    if any(word in message_lower for word in ['analyze', 'pdf', 'excel', 'spreadsheet', 'document', 'summary', 'points', 'data']):
        # Check for uploaded files (works for both authenticated and guest users)
        all_user_files = {}

        # If authenticated, check their files
        if user_id:
            all_user_files.update(uploaded_files.get(user_id, {}))

        # Also check for guest files in this session
        for uid, files in uploaded_files.items():
            if uid.startswith('guest_'):
                all_user_files.update(files)

        if all_user_files:
            # Get the most recently uploaded file
            latest_file = max(all_user_files.items(), key=lambda x: x[1]['upload_time'])
            file_path = latest_file[1]['path']
            filename = latest_file[0]

            print(f"Analyzing PDF: {filename}")

            try:
                result = document_analyzer.analyze_document_full(file_path)

                if result['success']:
                    # Determine document type for response
                    doc_icon = "📄" if filename.lower().endswith('.pdf') else "📊"
                    doc_type = "PDF" if filename.lower().endswith('.pdf') else "Excel"
                    response_text = f"""{doc_icon} {doc_type} Analysis Complete for "{filename}"

🔍 Summary:
{result['summary']}

📊 Processed {result['chunks_processed']} sections of the document.

💡 You can ask me specific questions about the content!"""

                    return jsonify({"reply": response_text})
                else:
                    return jsonify({"reply": f"❌ Could not analyze PDF: {result['error']}"})

            except Exception as e:
                print(f"PDF analysis error: {e}")
                if "timeout" in str(e).lower():
                    return jsonify({"reply": f"⏱️ PDF analysis timed out. The document might be too large or Ollama is slow. Try:\n1. Restart Ollama: `ollama serve`\n2. Use a smaller PDF\n3. Try again in a moment"})
                elif "connection" in str(e).lower():
                    return jsonify({"reply": f"🔌 Cannot connect to Ollama. Please:\n1. Start Ollama: `ollama serve`\n2. Run: `ollama run tinyllama`\n3. Try uploading again"})
                else:
                    return jsonify({"reply": f"❌ Error analyzing PDF: {str(e)}"})
        else:
            return jsonify({"reply": "📁 No documents uploaded yet. Please upload a PDF or Excel file first, then ask me to analyze it."})

    # Regular chat with TinyLlama
    try:
        # Connect to Ollama's API running locally
        response = requests.post(
            'http://localhost:11434/api/chat',
            json={
                "model": "tinyllama",
                "messages": [{"role": "user", "content": user_message}],
                "stream": stream_response
            },
            timeout=30,
            stream=stream_response
        )

        if response.status_code != 200:
            print(f"Ollama API error: {response.status_code} - {response.text}")
            raise requests.exceptions.ConnectionError("Ollama not responding")

        # Handle streaming vs non-streaming responses
        if stream_response:
            # Return streaming response
            def generate_stream():
                try:
                    full_content = ""
                    for line in response.iter_lines():
                        if line:
                            line_data = json.loads(line.decode('utf-8'))
                            if 'message' in line_data and 'content' in line_data['message']:
                                content = line_data['message']['content']
                                full_content += content
                                yield f"data: {json.dumps({'content': content})}\n\n"

                            # Check if this is the final message
                            if line_data.get('done', False):
                                yield f"data: {json.dumps({'done': True, 'full_content': full_content})}\n\n"
                                break
                except Exception as e:
                    print(f"Streaming error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return Response(generate_stream(),
                          mimetype='text/plain',
                          headers={'Cache-Control': 'no-cache',
                                 'Connection': 'keep-alive',
                                 'Access-Control-Allow-Origin': '*'})
        else:
            # Handle non-streaming response
            response_data = response.json()
            print(f"OLLAMA response: {json.dumps(response_data, indent=2)}")

            # Extract the assistant's reply from Ollama response
            if "message" in response_data and "content" in response_data["message"]:
                reply = response_data["message"]["content"]
            else:
                reply = "No response from AI model"

            return jsonify({"reply": reply})

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Ollama API. Using fallback response.")
        # Improved fallback responses based on user message content
        fallback_reply = generate_fallback_response(user_message, user_id)
        print(f"Sending fallback response: {fallback_reply}")
        return jsonify({"reply": fallback_reply})

    except requests.exceptions.Timeout:
        print("ERROR: Ollama API timeout. Using fallback response.")
        fallback_reply = generate_fallback_response(user_message, user_id)
        print(f"Sending timeout fallback response: {fallback_reply}")
        return jsonify({"reply": fallback_reply})

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"reply": f"AI backend error: {str(e)}"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        # Get user info if available (optional authentication)
        user_id = session.get('user_id')
        user = get_current_user()

        # Create a guest user ID if not authenticated
        if not user_id:
            user_id = f"guest_{secrets.token_hex(8)}"
            print(f"Guest upload with ID: {user_id}")

        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Check file type
        allowed_extensions = ['.pdf', '.xlsx', '.xls']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return jsonify({"error": "Only PDF and Excel files (.pdf, .xlsx, .xls) are supported"}), 400

        # Create user-specific uploads directory
        upload_dir = os.path.join('uploads', user_id)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        # Initialize user files storage if not exists
        if user_id not in uploaded_files:
            uploaded_files[user_id] = {}

        # Store file info for this user
        uploaded_files[user_id][filename] = {
            'path': file_path,
            'upload_time': datetime.now().isoformat(),
            'size': os.path.getsize(file_path)
        }

        # Different messages for authenticated vs guest users
        if user:
            print(f"File uploaded by {user['username']}: {filename} ({uploaded_files[user_id][filename]['size']} bytes)")
            message = f"✅ PDF uploaded successfully! Now you can ask me to 'analyze the PDF' or ask questions about it."
        else:
            print(f"File uploaded by guest {user_id}: {filename} ({uploaded_files[user_id][filename]['size']} bytes)")
            message = f"✅ PDF uploaded successfully! You can analyze it in this session. For persistent file storage, please log in."

        return jsonify({
            "filename": filename,
            "message": message,
            "size": uploaded_files[user_id][filename]['size']
        })

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/api/files', methods=['GET'])
@require_auth
def list_files():
    """List uploaded files for current user"""
    user_id = session.get('user_id')
    user_files = uploaded_files.get(user_id, {})

    return jsonify({
        "files": [
            {
                "name": name,
                "size": info["size"],
                "upload_time": info["upload_time"]
            }
            for name, info in user_files.items()
        ]
    })

@app.route('/api/user/chats', methods=['GET'])
@require_auth
def get_user_chats():
    """Get user's chat history"""
    user = get_current_user()

    if user and 'chat_history' in user:
        return jsonify({"chats": user['chat_history']})
    else:
        return jsonify({"chats": {}})

@app.route('/api/user/chats', methods=['POST'])
@require_auth
def save_user_chats():
    """Save user's chat history"""
    try:
        user_id = session.get('user_id')
        chats_data = request.get_json()

        if user_id in users_db:
            users_db[user_id]['chat_history'] = chats_data.get('chats', {})
            # Also save to file for persistence
            save_user_to_file(user_id, users_db[user_id])
            return jsonify({"success": True, "message": "Chats saved successfully"})
        else:
            return jsonify({"success": False, "message": "User not found"}), 404

    except Exception as e:
        print(f"Error saving chats: {str(e)}")
        return jsonify({"success": False, "message": "Failed to save chats"}), 500

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    print("Make sure Ollama is running with: ollama run tinyllama")
    print("Document Analysis Features:")
    print("  - Upload PDF and Excel files (.pdf, .xlsx, .xls)")
    print("  - Ask 'analyze the document' to get summary")
    print("  - Ask questions about uploaded content")

    # Install required packages reminder
    try:
        import PyPDF2
        import pdfplumber
        print(" PDF processing libraries available")
    except ImportError as e:
        print(f"Missing PDF libraries: {e}")
        print("Install with: pip install PyPDF2 pdfplumber")

    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Failed to start server: {e}")
        