import os
import json
from database import init_database, create_user_in_db, get_user_from_db

def migrate_file_users_to_postgresql():
    """Migrate users from file storage to PostgreSQL"""
    
    print("🚀 Migrating Users from File Storage to PostgreSQL")
    print("=" * 60)
    
    # Initialize database
    if not init_database():
        print("❌ Failed to initialize PostgreSQL database")
        return False
    
    # Check users directory
    if not os.path.exists('users'):
        print("❌ No users directory found")
        return False
    
    user_files = [f for f in os.listdir('users') if f.endswith('.json')]
    
    if not user_files:
        print("❌ No user files found")
        return False
    
    print(f"📁 Found {len(user_files)} users in file storage")
    
    migrated_count = 0
    skipped_count = 0
    
    for user_file in user_files:
        try:
            # Read user data from file
            with open(f'users/{user_file}', 'r') as f:
                user_data = json.load(f)
            
            user_id = user_data['id']
            email = user_data['email']
            username = user_data['username']
            password_hash = user_data['password_hash']
            
            print(f"\n👤 Processing: {username} ({email})")
            
            # Check if user already exists in PostgreSQL
            existing_user = get_user_from_db(email=email)
            if existing_user:
                print(f"   ⚠️ User already exists in PostgreSQL, skipping")
                skipped_count += 1
                continue
            
            # Create user directly in database (bypass password hashing since it's already hashed)
            success = create_user_in_postgresql_direct(user_id, email, username, password_hash, user_data.get('created_at'), user_data.get('chat_history', {}))
            
            if success:
                print(f"   ✅ Successfully migrated to PostgreSQL")
                migrated_count += 1
            else:
                print(f"   ❌ Failed to migrate")
                
        except Exception as e:
            print(f"   ❌ Error processing {user_file}: {e}")
    
    print(f"\n📊 Migration Summary:")
    print(f"   ✅ Migrated: {migrated_count} users")
    print(f"   ⚠️ Skipped: {skipped_count} users")
    print(f"   📁 Total files: {len(user_files)} users")
    
    if migrated_count > 0:
        print(f"\n🎉 Migration completed! You can now login with your existing credentials.")
    
    return migrated_count > 0

def create_user_in_postgresql_direct(user_id, email, username, password_hash, created_at, chat_history):
    """Create user in PostgreSQL with pre-hashed password"""
    try:
        from database import get_db_session, User
        from datetime import datetime
        import json
        
        session = get_db_session()
        
        # Parse created_at if it's a string
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                created_at = datetime.utcnow()
        elif not created_at:
            created_at = datetime.utcnow()
        
        # Create new user with existing password hash
        new_user = User(
            id=user_id,
            email=email,
            username=username,
            password_hash=password_hash,  # Use existing hash
            created_at=created_at,
            chat_history=json.dumps(chat_history) if chat_history else '{}'
        )
        
        session.add(new_user)
        session.commit()
        session.close()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def verify_migration():
    """Verify that users were migrated successfully"""
    print("\n🔍 Verifying Migration...")
    print("=" * 40)
    
    try:
        from database import get_db_session, User
        
        session = get_db_session()
        users = session.query(User).all()
        
        print(f"✅ PostgreSQL now has {len(users)} users:")
        for user in users:
            print(f"   👤 {user.username} ({user.email})")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error verifying: {e}")

if __name__ == "__main__":
    if migrate_file_users_to_postgresql():
        verify_migration()
        print("\n🎯 Next Steps:")
        print("   1. Try logging in with your existing credentials")
        print("   2. Your chat history should be preserved")
        print("   3. New users will be saved to PostgreSQL")
    else:
        print("\n💥 Migration failed!")
        print("   Your app will continue using file storage")
