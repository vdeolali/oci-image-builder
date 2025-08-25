import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- START OF MODIFICATION ---
    # Load OCI configuration from environment variables
    OCI_CONFIG_FILE = os.path.expanduser('/Users/vdeolali/.oci/config') # Keeps the default location
    
    OCI_COMPARTMENT_OCID = os.getenv('OCI_COMPARTMENT_OCID')
    OCI_SUBNET_OCID = os.getenv('OCI_SUBNET_OCID')
    OCI_AVAILABILITY_DOMAIN = os.getenv('OCI_AVAILABILITY_DOMAIN')

    # Fail fast if essential configuration is missing
    if not all([OCI_COMPARTMENT_OCID, OCI_SUBNET_OCID, OCI_AVAILABILITY_DOMAIN]):
        raise ValueError("Essential OCI configuration environment variables are missing (OCI_COMPARTMENT_OCID, OCI_SUBNET_OCID, OCI_AVAILABILITY_DOMAIN)")
    # --- END OF MODIFICATION ---

