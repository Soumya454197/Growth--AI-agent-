import os
import json
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'growth_chat_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Fallback to individual components
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy setup
Base = declarative_base()
engine = None
SessionLocal = None

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(32), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    chat_history = Column(Text, default='{}')  # JSON string

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer, nullable=False)

def init_database():
    """Initialize database connection and create tables"""
    global engine, SessionLocal
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL, echo=False)
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ PostgreSQL database connected successfully")
        # Safely mask password in URL for logging
        masked_url = DATABASE_URL
        if DB_PASSWORD:
            masked_url = DATABASE_URL.replace(DB_PASSWORD, '***')
        print(f"📊 Database URL: {masked_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and credentials are correct")
        return False

def get_db_session():
    """Get database session"""
    if SessionLocal is None:
        raise Exception("Database not initialized. Call init_database() first.")
    return SessionLocal()

def create_user_in_db(user_id, email, username, password):
    """Create user in PostgreSQL database"""
    try:
        session = get_db_session()
        
        # Check if user already exists
        existing_user = session.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            session.close()
            return False, "User already exists"
        
        # Create new user
        new_user = User(
            id=user_id,
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            chat_history='{}'
        )
        
        session.add(new_user)
        session.commit()
        session.close()
        
        print(f"✅ User created in database: {username} ({email})")
        return True, "User created successfully"
        
    except Exception as e:
        print(f"❌ Error creating user in database: {e}")
        return False, str(e)

def get_user_from_db(email=None, user_id=None):
    """Get user from PostgreSQL database"""
    try:
        session = get_db_session()
        
        if email:
            user = session.query(User).filter(User.email == email).first()
        elif user_id:
            user = session.query(User).filter(User.id == user_id).first()
        else:
            session.close()
            return None
        
        if user:
            user_data = {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'password_hash': user.password_hash,
                'created_at': user.created_at.isoformat(),
                'chat_history': json.loads(user.chat_history) if user.chat_history else {}
            }
            session.close()
            return user_data
        
        session.close()
        return None
        
    except Exception as e:
        print(f"❌ Error getting user from database: {e}")
        return None

def update_user_chat_history(user_id, chat_history):
    """Update user's chat history in database"""
    try:
        session = get_db_session()
        
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.chat_history = json.dumps(chat_history)
            session.commit()
            session.close()
            return True
        
        session.close()
        return False
        
    except Exception as e:
        print(f"❌ Error updating chat history: {e}")
        return False

def save_uploaded_file_to_db(user_id, filename, file_path, file_size):
    """Save uploaded file info to database"""
    try:
        session = get_db_session()
        
        uploaded_file = UploadedFile(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size
        )
        
        session.add(uploaded_file)
        session.commit()
        session.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving file to database: {e}")
        return False

def get_user_files_from_db(user_id):
    """Get user's uploaded files from database"""
    try:
        session = get_db_session()
        
        files = session.query(UploadedFile).filter(UploadedFile.user_id == user_id).all()
        
        file_list = []
        for file in files:
            file_list.append({
                'name': file.filename,
                'path': file.file_path,
                'upload_time': file.upload_time.isoformat(),
                'size': file.file_size
            })
        
        session.close()
        return file_list
        
    except Exception as e:
        print(f"❌ Error getting user files: {e}")
        return []

# Test database connection
if __name__ == "__main__":
    if init_database():
        print("🎉 Database setup completed successfully!")
    else:
        print("💥 Database setup failed!")
