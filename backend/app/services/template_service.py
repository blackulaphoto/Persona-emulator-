"""
Template Service

Handles loading clinical templates from JSON files and creating personas from templates.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import uuid
import logging

from app.models.clinical_template import ClinicalTemplate
from app.models.persona import Persona

logger = logging.getLogger(__name__)

# Path to template JSON files
# In production, these might be in a data/ directory or loaded from a database
TEMPLATE_JSON_DIR = Path(__file__).parent.parent.parent / "data" / "templates"
# Fallback to remix component directory if data/templates doesn't exist
FALLBACK_TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "remix component" / "step 1"


def get_template_json_directory() -> Path:
    """Get the directory containing template JSON files."""
    if TEMPLATE_JSON_DIR.exists():
        return TEMPLATE_JSON_DIR
    elif FALLBACK_TEMPLATE_DIR.exists():
        return FALLBACK_TEMPLATE_DIR
    else:
        # Return the fallback path anyway - will raise error when trying to read
        return FALLBACK_TEMPLATE_DIR


def load_template_from_json(json_path: Path) -> Dict:
    """
    Load a template from a JSON file.
    
    Args:
        json_path: Path to JSON file
        
    Returns:
        Dictionary with template data
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        template_data = json.load(f)
    
    return template_data


def create_template_from_dict(db: Session, template_data: Dict) -> ClinicalTemplate:
    """
    Create a ClinicalTemplate database record from template dictionary.
    
    Args:
        db: Database session
        template_data: Template data dictionary from JSON
        
    Returns:
        Created ClinicalTemplate object
    """
    # Use provided ID or generate one from template filename
    template_id = template_data.get("id") or str(uuid.uuid4())
    
    # Check if template already exists
    existing = db.query(ClinicalTemplate).filter(ClinicalTemplate.id == template_id).first()
    if existing:
        logger.info(f"Template {template_id} already exists, skipping")
        return existing
    
    template = ClinicalTemplate(
        id=template_id,
        name=template_data["name"],
        disorder_type=template_data["disorder_type"],
        description=template_data["description"],
        clinical_rationale=template_data["clinical_rationale"],
        baseline_age=template_data["baseline_age"],
        baseline_gender=template_data.get("baseline_gender"),
        baseline_background=template_data["baseline_background"],
        baseline_personality=template_data["baseline_personality"],
        baseline_attachment_style=template_data.get("baseline_attachment_style", "secure"),
        predefined_experiences=template_data.get("predefined_experiences", []),
        predefined_interventions=template_data.get("predefined_interventions", []),
        expected_outcomes=template_data.get("expected_outcomes", {}),
        citations=template_data.get("citations", []),
        remix_suggestions=template_data.get("remix_suggestions", [])
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


def populate_templates_database(db: Session) -> int:
    """
    Populate database with templates from JSON files.
    
    Looks for all .json files in the template directory and loads them.
    
    Args:
        db: Database session
        
    Returns:
        Number of templates loaded
    """
    template_dir = get_template_json_directory()
    
    if not template_dir.exists():
        logger.warning(f"Template directory {template_dir} does not exist. Creating empty database.")
        return 0
    
    json_files = list(template_dir.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No JSON template files found in {template_dir}")
        return 0
    
    loaded_count = 0
    
    for json_file in json_files:
        try:
            template_data = load_template_from_json(json_file)
            create_template_from_dict(db, template_data)
            loaded_count += 1
            logger.info(f"Loaded template: {template_data.get('name', json_file.name)}")
        except Exception as e:
            logger.error(f"Error loading template from {json_file}: {e}")
            continue
    
    return loaded_count


def create_persona_from_template(
    db: Session,
    template_id: str,
    owner_id: Optional[str] = None,
    custom_name: Optional[str] = None
) -> Persona:
    """
    Create a persona from a clinical template.
    
    Args:
        db: Database session
        template_id: Template ID to use
        owner_id: Optional owner ID (for multi-user systems)
        custom_name: Optional custom name for persona
        
    Returns:
        Created Persona object
    """
    # Get template
    template = db.query(ClinicalTemplate).filter(ClinicalTemplate.id == template_id).first()
    if not template:
        raise ValueError(f"Template {template_id} not found")
    
    # Generate persona name
    if custom_name:
        persona_name = custom_name
    else:
        persona_name = f"Case Study: {template.disorder_type}"
    
    # Create persona with template baseline
    # Note: Persona model uses current_personality as the working state
    # Template's baseline_personality becomes the persona's initial current_personality
    baseline_personality = template.baseline_personality.copy()
    
    persona = Persona(
        owner_id=owner_id,
        name=persona_name,
        baseline_age=template.baseline_age,
        baseline_gender=template.baseline_gender,
        baseline_background=template.baseline_background,
        current_personality=baseline_personality,
        current_attachment_style=template.baseline_attachment_style,
        current_age=template.baseline_age,
        current_trauma_markers=[]
    )
    
    db.add(persona)
    db.commit()
    db.refresh(persona)
    
    return persona


def get_template_experiences(template_id: str, db: Optional[Session] = None) -> List[Dict]:
    """
    Get predefined experiences for a template.
    
    Args:
        template_id: Template ID
        db: Optional database session (if not provided, reads from JSON)
        
    Returns:
        List of experience dictionaries
    """
    if db:
        template = db.query(ClinicalTemplate).filter(ClinicalTemplate.id == template_id).first()
        if template:
            return template.predefined_experiences or []
    
    # Fallback: try to load from JSON by searching all JSON files
    template_dir = get_template_json_directory()
    
    if template_dir.exists():
        # Try exact filename match first
        json_file = template_dir / f"{template_id}.json"
        if not json_file.exists():
            # Search all JSON files for matching ID
            for json_file in template_dir.glob("*.json"):
                try:
                    template_data = load_template_from_json(json_file)
                    if template_data.get("id") == template_id:
                        return template_data.get("predefined_experiences", [])
                except Exception:
                    continue
        else:
            template_data = load_template_from_json(json_file)
            return template_data.get("predefined_experiences", [])
    
    raise FileNotFoundError(f"Template {template_id} not found in database or JSON files")


def get_template_interventions(template_id: str, db: Optional[Session] = None) -> List[Dict]:
    """
    Get predefined interventions for a template.
    
    Args:
        template_id: Template ID
        db: Optional database session (if not provided, reads from JSON)
        
    Returns:
        List of intervention dictionaries
    """
    if db:
        template = db.query(ClinicalTemplate).filter(ClinicalTemplate.id == template_id).first()
        if template:
            return template.predefined_interventions or []
    
    # Fallback: try to load from JSON by searching all JSON files
    template_dir = get_template_json_directory()
    
    if template_dir.exists():
        # Try exact filename match first
        json_file = template_dir / f"{template_id}.json"
        if not json_file.exists():
            # Search all JSON files for matching ID
            for json_file in template_dir.glob("*.json"):
                try:
                    template_data = load_template_from_json(json_file)
                    if template_data.get("id") == template_id:
                        return template_data.get("predefined_interventions", [])
                except Exception:
                    continue
        else:
            template_data = load_template_from_json(json_file)
            return template_data.get("predefined_interventions", [])
    
    return []  # Interventions are optional


def get_all_disorder_types(db: Session) -> List[str]:
    """
    Get list of all unique disorder types from templates in database.
    
    Args:
        db: Database session
        
    Returns:
        List of disorder type strings (e.g., ["BPD", "C-PTSD", "Social_Anxiety"])
    """
    # Ensure templates are loaded
    template_count = db.query(ClinicalTemplate).count()
    if template_count == 0:
        populate_templates_database(db)
    
    disorder_types = db.query(ClinicalTemplate.disorder_type).distinct().all()
    return [dt[0] for dt in disorder_types] if disorder_types else []


def get_templates_by_disorder(db: Session, disorder_type: str) -> List[ClinicalTemplate]:
    """
    Get all templates for a specific disorder type.
    
    Args:
        db: Database session
        disorder_type: Disorder type to filter by
        
    Returns:
        List of ClinicalTemplate objects
    """
    # Ensure templates are loaded
    template_count = db.query(ClinicalTemplate).count()
    if template_count == 0:
        populate_templates_database(db)
    
    templates = db.query(ClinicalTemplate).filter(
        ClinicalTemplate.disorder_type == disorder_type
    ).all()
    
    return templates

