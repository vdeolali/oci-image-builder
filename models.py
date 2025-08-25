from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ImageBuild(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cloud_provider = db.Column(db.String(50), nullable=False)
    
    # --- START OF MODIFICATION ---
    # Add the profile field, making it required.
    oci_profile = db.Column(db.String(100), nullable=False)
    # --- END OF MODIFICATION ---

    base_image = db.Column(db.String(255), nullable=False)
    packages = db.Column(db.Text, nullable=True)
    shape = db.Column(db.String(100), nullable=False)
    ocpus = db.Column(db.Integer, nullable=True)
    memory_in_gbs = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), default='Queued')
    packer_output = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ImageBuild {self.id} - {self.base_image}>'

