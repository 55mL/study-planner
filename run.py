
import sys
import subprocess
from app import create_app, db
from flask_migrate import upgrade, migrate, init, stamp
import os
from alembic.util.exc import CommandError
import sqlite3
from app.utils.utils import log

app = create_app()

def unlock_database():
    try:
        db_path = os.path.join(os.getcwd(), 'instance', 'data.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.close()
            print("Database unlocked successfully")
    except Exception as e:
        print(f"Error unlocking database: {e}")

def setup_database():
    try:
        unlock_database()
        if not os.path.exists("migrations"):
            print("Initializing new database...")
            init()
            stamp()
        # อัปเกรด DB ให้ตรงกับ migration ล่าสุด
        print("Upgrading database to latest revision...")
        try:
            migrate(message="auto migration")
        except CommandError as e:
            print("Migration failed, attempting to upgrade first...")
            upgrade()
            migrate(message="auto migration")
        upgrade()
        print("Database migration completed successfully")
    except Exception as e:
        print(f"Database setup error: {e}")
        raise

def run_tests():
    print("Running tests...")
    # ใช้ pytest ถ้ามี, fallback เป็น unittest
    try:
        import pytest
        result = subprocess.run([sys.executable, '-m', 'pytest', 'tests'], check=False)
        sys.exit(result.returncode)
    except ImportError:
        import unittest
        tests = unittest.TestLoader().discover('tests')
        runner = unittest.TextTestRunner()
        result = runner.run(tests)
        sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        with app.app_context():
            setup_database()
        log("✅ Starting Flask app with debug logger", name="system")
        port = int(os.environ.get("PORT", 5000))  # Render/Heroku จะส่งค่า PORT มา
        app.run(host="0.0.0.0", port=port, debug=False)

