import pandas as pd
import pathlib
import uuid
import re

class OutputDataframe:
    """
    Outputs dataframe regardless of the file
    """
    def __init__(self, input_file):
        extension = pathlib.Path(input_file).suffix
        if extension in ['.csv', '.xlsx', '.xls']:
            self.input_file = input_file
            self.extension = extension
        else:
            raise ValueError("Incorrect File Type")

    def convert_to_dataframe(self):
        if self.extension == '.csv':
            return pd.read_csv(self.input_file)
        elif self.extension == '.xlsx':
            return pd.read_excel(self.input_file, engine='openpyxl')
        elif self.extension == '.xls':
            return pd.read_excel(self.input_file)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename(filename):
    """
    Sanitize the filename by removing unsafe characters.
    
    Args:
    - filename: The original name of the uploaded file.
    
    Returns:
    - A sanitized filename.
    """
    # Replace unsafe characters with underscores
    sanitized = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    sanitized = re.sub(r'[\s]+', '_', sanitized)
    return sanitized

def secure_filename(user_id, original_filename):
    """
    Generate a secure, unique filename associated with a specific user.
    
    Args:
    - user_id: The unique identifier for the user (e.g., user ID).
    - original_filename: The original name of the uploaded file.
    
    Returns:
    - A secure, unique filename within the user's folder.
    """
    # Generate a unique identifier for the file
    unique_id = str(uuid.uuid4())

    # Sanitize the filename
    valid_filename = sanitize_filename(original_filename)

    # Combine the unique identifier with the sanitized filename
    return f"{unique_id}_{valid_filename}"
