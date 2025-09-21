import sys
import traceback
from dotenv import load_dotenv

print("--- Starting Database Connection Debugger ---")

try:
    print("1. Loading .env file...")
    load_dotenv()
    print("   .env file loaded successfully.")

    print("2. Importing 'create_app' from the 'app' package...")
    from app import create_app
    print("   'create_app' imported successfully.")

    print("3. Creating the Flask application instance...")
    app = create_app()
    print("   Flask application instance created.")

    print("4. Pushing application context...")
    with app.app_context():
        print("   Application context pushed successfully.")
        
        print("5. Importing 'User' model and 'db' instance...")
        from app.models import User
        from app import db
        print("   Models imported successfully.")

        print("6. Attempting to connect to the database with a simple query...")
        # This is the line that will force a connection and likely fail
        first_user = User.query.first()
        print("   Database query successful!")
        if first_user:
            print(f"   Successfully retrieved user: {first_user.name}")
        else:
            print("   Database is empty, but the connection worked.")

    print("\n--- DATABASE DEBUG SUCCESS ---")
    print("Application and database connection appear to be configured correctly.")

except Exception as e:
    print("\n--- !!! DATABASE DEBUG FAILURE !!! ---")
    print("An error occurred. This is most likely a DATABASE CONNECTION or CONFIGURATION issue.")
    print(f"\n[Error Type]: {type(e).__name__}")
    print(f"[Error Message]: {e}")
    print("\n--- [FULL PYTHON TRACEBACK] ---")
    traceback.print_exc()
    print("---------------------------------")

finally:
    print("\n--- Debug Runner Finished ---")
    sys.exit(0)