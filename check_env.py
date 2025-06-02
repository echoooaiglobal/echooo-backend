# check_env.py
# Quick script to verify your .env file is being loaded correctly

import os
from dotenv import load_dotenv

def check_env_file():
    print("🔍 Checking .env file...")
    print("=" * 50)
    
    # Check if .env file exists
    env_file_path = ".env"
    if os.path.exists(env_file_path):
        print("✅ .env file found")
        
        # Read .env file content
        with open(env_file_path, 'r') as f:
            content = f.read()
        
        # Show DB-related lines
        lines = content.split('\n')
        print("\n📄 Database-related lines in .env:")
        print("-" * 40)
        for line in lines:
            if line.strip() and any(db_key in line for db_key in ['DB_', 'DATABASE']):
                # Hide password for security
                if 'PASSWORD' in line:
                    key, value = line.split('=', 1)
                    print(f"{key}={'*' * len(value)}")
                else:
                    print(line)
    else:
        print("❌ .env file not found!")
        return
    
    print("\n🔄 Loading environment variables...")
    load_dotenv()
    
    # Check loaded environment variables
    print("\n📋 Loaded Environment Variables:")
    print("-" * 40)
    db_vars = ['DB_TYPE', 'DB_USERNAME', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME']
    
    for var in db_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"{var}: {'*' * len(value)}")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: ❌ NOT SET")
    
    # Show what database will be connected to
    db_name = os.getenv('DB_NAME')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    
    print(f"\n🎯 Will connect to:")
    print(f"Database: {db_name}")
    print(f"Host: {db_host}:{db_port}")

if __name__ == "__main__":
    check_env_file()