"""
File Utilities
Helper functions for file operations
"""
import os
import uuid
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Optional
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    if not filename:
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', set())


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension"""
    extension = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{extension}" if extension else unique_id


def save_uploaded_file(file, upload_folder: Optional[Path] = None) -> Tuple[str, str]:
    """
    Save uploaded file with unique name
    
    Returns:
        Tuple of (filepath, original_filename)
    """
    if not file or not file.filename:
        raise ValueError("No file provided")
    
    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed: {get_file_extension(file.filename)}")
    
    # Use provided folder or default
    folder = upload_folder or current_app.config.get('UPLOAD_FOLDER')
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    
    # Generate secure filename
    original_filename = secure_filename(file.filename)
    unique_filename = generate_unique_filename(original_filename)
    filepath = folder / unique_filename
    
    # Save file
    file.save(str(filepath))
    logger.info(f"File saved: {filepath}")
    
    return str(filepath), original_filename


def get_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """Calculate file hash"""
    hash_func = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(filepath)


def delete_file(filepath: str) -> bool:
    """Safely delete a file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"File deleted: {filepath}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file {filepath}: {e}")
        return False


def is_image_file(filename: str) -> bool:
    """Check if file is an image"""
    image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
    extension = get_file_extension(filename)
    return extension in image_extensions


def is_document_file(filename: str) -> bool:
    """Check if file is a document"""
    doc_extensions = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'epub', 'txt'}
    extension = get_file_extension(filename)
    return extension in doc_extensions


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """
    Clean up files older than max_age_hours
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum file age in hours
    """
    import time
    
    if not directory.exists():
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0
    
    for filepath in directory.iterdir():
        if filepath.is_file():
            file_age = current_time - filepath.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    filepath.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting old file {filepath}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old files from {directory}")
