"""
Restore Original Clinical Templates

This script loads the 3 original JSON templates (C-PTSD, Social Anxiety, BPD)
from backend/data/templates/ into the database WITHOUT removing the 6 new templates.
"""
import sys
import os
from pathlib import Path

# Add backend directory to path so we can import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.template_service import populate_templates_database
from app.core.database import Base

def main():
    """Load original templates from JSON files"""
    # Use the dev.db database
    db_path = backend_dir / "dev.db"
    engine = create_engine(f'sqlite:///{db_path}')

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("Loading original templates from JSON files...")
        print(f"Database: {db_path}")

        # This function loads all JSON templates from backend/data/templates/
        # It will skip templates that already exist (by checking template name)
        count = populate_templates_database(db)

        print(f"\n[SUCCESS] Processed {count} templates from JSON files")
        print("Note: Existing templates were preserved (not overwritten)")

    except Exception as e:
        print(f"\n[ERROR] Error loading templates: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
