from database import get_db_session, User
import json

def check_users_in_database():
    """Check what users exist in PostgreSQL database"""
    try:
        session = get_db_session()
        users = session.query(User).all()
        
        print("🔍 Users in PostgreSQL database:")
        print("=" * 40)
        
        if not users:
            print("❌ No users found in PostgreSQL database")
            print("💡 This is why login is failing!")
        else:
            for user in users:
                print(f"✅ User: {user.username}")
                print(f"   Email: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Created: {user.created_at}")
                print("-" * 30)
        
        session.close()
        return len(users)
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return 0

def check_file_users():
    """Check what users exist in file storage"""
    import os
    
    print("\n📁 Users in file storage:")
    print("=" * 40)
    
    if not os.path.exists('users'):
        print("❌ No users directory found")
        return 0
    
    user_files = [f for f in os.listdir('users') if f.endswith('.json')]
    
    if not user_files:
        print("❌ No user files found")
        return 0
    
    for user_file in user_files:
        try:
            with open(f'users/{user_file}', 'r') as f:
                user_data = json.load(f)
                print(f"✅ User: {user_data['username']}")
                print(f"   Email: {user_data['email']}")
                print(f"   ID: {user_data['id']}")
                print(f"   File: {user_file}")
                print("-" * 30)
        except Exception as e:
            print(f"❌ Error reading {user_file}: {e}")
    
    return len(user_files)

if __name__ == "__main__":
    print("🚀 User Database Check")
    print("=" * 50)
    
    # Check PostgreSQL
    pg_users = check_users_in_database()
    
    # Check file storage
    file_users = check_file_users()
    
    print(f"\n📊 Summary:")
    print(f"   PostgreSQL users: {pg_users}")
    print(f"   File storage users: {file_users}")
    
    if pg_users == 0 and file_users > 0:
        print("\n💡 Solution: Your users are in file storage but app is using PostgreSQL!")
        print("   Options:")
        print("   1. Create a new account (will save to PostgreSQL)")
        print("   2. Migrate file users to PostgreSQL")
        print("   3. Temporarily switch back to file storage")
