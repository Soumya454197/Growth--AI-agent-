import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgresql_connection():
    """Test PostgreSQL connection with different configurations"""
    
    # Test configurations to try
    test_configs = [
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': ''
        },
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'postgres'
        },
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'password'
        }
    ]
    
    print("🔍 Testing PostgreSQL connections...")
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n📋 Test {i}: {config['user']}@{config['host']}:{config['port']}/{config['database']}")
        print(f"   Password: {'(empty)' if not config['password'] else '***'}")
        
        try:
            # Try to connect
            conn = psycopg2.connect(**config)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✅ SUCCESS! Connected to PostgreSQL")
            print(f"   Version: {version}")
            
            # Update .env with working configuration
            update_env_file(config)
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ Connection failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n💡 None of the default configurations worked.")
    print("   Please check:")
    print("   1. PostgreSQL service is running")
    print("   2. Your PostgreSQL password")
    print("   3. Database exists")
    
    return False

def update_env_file(config):
    """Update .env file with working configuration"""
    env_content = f"""# PostgreSQL Database Configuration
DB_HOST={config['host']}
DB_PORT={config['port']}
DB_NAME={config['database']}
DB_USER={config['user']}
DB_PASSWORD={config['password']}

# Database URL (alternative format)
DATABASE_URL=postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here-change-this-in-production

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=tinyllama

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216  # 16MB in bytes

# Security Configuration
SESSION_TIMEOUT=3600  # 1 hour in seconds
BCRYPT_ROUNDS=12

# Optional: External API Keys (if needed)
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here

# Development vs Production
ENVIRONMENT=development
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"✅ Updated .env file with working configuration")

def create_database_if_needed():
    """Create the growth_chat_db database if it doesn't exist"""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password=os.getenv('DB_PASSWORD', '')
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='growth_chat_db'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE growth_chat_db")
            print("✅ Created database 'growth_chat_db'")
        else:
            print("✅ Database 'growth_chat_db' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Could not create database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PostgreSQL Connection Test")
    print("=" * 40)
    
    if test_postgresql_connection():
        print("\n🎯 Creating application database...")
        create_database_if_needed()
        print("\n🎉 PostgreSQL setup complete!")
        print("   You can now run: python backend.py")
    else:
        print("\n💥 PostgreSQL setup failed!")
        print("   Your app will use file storage instead.")
