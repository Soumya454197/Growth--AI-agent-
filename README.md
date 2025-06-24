# Growth--AI-agent-
Growth Chatbot
A privacy-focused, local-first chatbot application that leverages the TinyLlama model via Ollama and PostgreSQL for persistent data storage. Built with Flask for robust web service delivery.

Overview
Growth Chatbot provides a secure, locally-hosted AI chat interface with document analysis capabilities. The application prioritizes user privacy by running AI models locally while maintaining chat history and user data in a PostgreSQL database.

Features
Local AI Processing: Powered by TinyLlama model through Ollama runtime
User Authentication: Secure signup, login, and session management
Document Analysis: PDF and Excel file upload with content summarization
Persistent Storage: PostgreSQL database for user data and chat history
Privacy-First: All AI processing occurs locally without external API calls
Web Interface: Clean, responsive Flask-based frontend
Architecture
├── backend.py              # Main Flask application
├── database.py             # SQLAlchemy models and database operations
├── migrate_users.py        # User data migration utilities
├── check_users.py          # Database inspection tools
├── test_db.py              # Database connection testing and initialization
├── .env                    # Environment configuration
├── requirements.txt        # Python dependencies
├── uploads/                # Document upload directory
├── users/                  # Legacy user data storage
├── login_signup/           # Authentication interface
└── static_/                # Main application interface
Prerequisites
Python 3.10 or higher
PostgreSQL 12+ (running locally)
Ollama runtime environment
Anaconda or virtualenv
Installation
1. Repository Setup
bash
git clone https://github.com/yourusername/growth-chatbot.git
cd growth-chatbot
2. Environment Configuration
Create and activate a conda environment:

bash
conda create -n growthbot python=3.10 -y
conda activate growthbot
3. Dependency Installation
bash
pip install -r requirements.txt
4. Database Configuration
Ensure PostgreSQL is running on the default port (5432). Initialize the database:

bash
python test_db.py
This script will:

Verify PostgreSQL connectivity
Create the growth_chat_db database if it doesn't exist
Generate or update the .env configuration file
5. AI Model Setup
Install and configure Ollama with the TinyLlama model:

bash
# Install Ollama (if not already installed)
# Follow instructions at https://ollama.com/

# Pull the TinyLlama model
ollama pull tinyllama

# Start Ollama service
ollama serve
6. Application Launch
Start the Flask development server:

bash
python backend.py
Access the application at http://localhost:5000

Configuration
The application uses environment variables defined in .env:

env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=growth_chat_db
DB_USER=postgres
DB_PASSWORD=your_password

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=tinyllama

# Application Settings
UPLOAD_FOLDER=uploads
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
Database Management
Migration from File-based Storage
If migrating from a previous file-based user storage system:

bash
python migrate_users.py
User Data Inspection
To inspect current user storage status:

bash
python check_users.py
API Endpoints
POST /signup - User registration
POST /login - User authentication
POST /logout - Session termination
POST /chat - Chat message processing
POST /upload - Document upload and analysis
GET /history - Chat history retrieval
Security Considerations
All user passwords are hashed using secure algorithms
Session management through Flask-Session
File uploads are validated and stored securely
Local AI processing ensures data privacy
Development
Running Tests
bash
python test_db.py
Database Schema Updates
After modifying database models, update the schema:

bash
python database.py
Deployment
For production deployment:

Set FLASK_ENV=production in .env
Configure a production-grade WSGI server (e.g., Gunicorn)
Set up proper PostgreSQL user permissions
Configure reverse proxy (e.g., Nginx)
Contributing
Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request
License
This project is licensed under the MIT License. See the LICENSE file for details.

Support
For issues and questions, please open an issue on GitHub or contact the development team.

Acknowledgments
Ollama for local AI model serving
TinyLlama for the base language model
Flask community for the web framework
PostgreSQL for robust data storage
