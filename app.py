import os
import threading
from flask import Flask, render_template, redirect, url_for, flash, jsonify, request
from forms import ImageBlueprintForm
from models import db, ImageBuild
from packer_utils import run_packer_build
from oci_utils import get_oci_images, get_oci_profiles, get_available_shapes

# --- START OF THE DEFINITIVE FIX ---

# Define the absolute base directory of THIS file.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def create_app():
    """
    Creates and configures the Flask application.
    """
    app = Flask(__name__)

    # Configure the app directly here to force the correct settings.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'a-very-secret-key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 1. Define the absolute path for the instance folder.
    instance_path = os.path.join(BASE_DIR, 'instance')
    
    # 2. Define the absolute path for the database file.
    database_path = os.path.join(instance_path, 'app.db')
    
    # 3. Set the database URI using the absolute path. Note the 'sqlite:///' prefix.
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'

    # Load OCI configuration from environment variables (from .env file)
    app.config['OCI_CONFIG_FILE'] = os.path.expanduser('~/.oci/config')
    app.config['OCI_COMPARTMENT_OCID'] = os.getenv('OCI_COMPARTMENT_OCID')
    app.config['OCI_SUBNET_OCID'] = os.getenv('OCI_SUBNET_OCID')
    app.config['OCI_AVAILABILITY_DOMAIN'] = os.getenv('OCI_AVAILABILITY_DOMAIN')
    
    # 4. Ensure the instance folder exists before we do anything else.
    try:
        os.makedirs(instance_path)
    except OSError:
        pass # The directory already exists, which is fine.

    # --- END OF THE DEFINITIVE FIX ---

    # Initialize database extension
    db.init_app(app)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        form = ImageBlueprintForm()
        oci_config_file = app.config['OCI_CONFIG_FILE']
        compartment_ocid = app.config['OCI_COMPARTMENT_OCID']

        form.oci_profile.choices = [(p, p) for p in get_oci_profiles(oci_config_file)]

        if request.method == 'POST':
           selected_profile = form.oci_profile.data
           form.base_image.choices = get_oci_images(compartment_ocid, oci_config_file, selected_profile)
           form.shape.choices = get_available_shapes(compartment_ocid, oci_config_file, selected_profile)

        if form.validate_on_submit():
           new_build = ImageBuild(
               cloud_provider=form.cloud_provider.data,
            
            # --- THIS IS THE MISSING LINE THAT FIXES THE BUG ---
               oci_profile=form.oci_profile.data,
            # ---------------------------------------------------
            
               base_image=form.base_image.data,
               packages=form.packages.data,
               shape=form.shape.data,
               ocpus=form.ocpus.data if 'Flex' in form.shape.data else None,
               memory_in_gbs=form.memory_in_gbs.data if 'Flex' in form.shape.data else None
           )
           db.session.add(new_build)
           db.session.commit()

           build_thread = threading.Thread(target=run_packer_build, args=(app, new_build.id))
           build_thread.start()
        
           selected_image_name = dict(form.base_image.choices).get(form.base_image.data, 'Unknown Image')
           flash(f"Started image build (ID: {new_build.id}) for {selected_image_name} on shape {new_build.shape}.", 'success')
           return redirect(url_for('build_history'))

        return render_template('index.html', form=form)


    @app.route('/api/shapes/<profile_name>')
    def get_shapes_for_profile(profile_name):
        shapes = get_available_shapes(app.config['OCI_COMPARTMENT_OCID'], app.config['OCI_CONFIG_FILE'], profile_name)
        return jsonify([{"id": name, "name": name} for name, name in shapes])

    @app.route('/api/images/<profile_name>')
    def get_images_for_profile(profile_name):
        images = get_oci_images(app.config['OCI_COMPARTMENT_OCID'], app.config['OCI_CONFIG_FILE'], profile_name)
        return jsonify([{"id": ocid, "name": name} for ocid, name in images])

    @app.route('/builds')
    def build_history():
        builds = ImageBuild.query.order_by(ImageBuild.created_at.desc()).all()
        return render_template('builds.html', builds=builds)

    return app

if __name__ == '__main__':
    app = create_app()

    # This context block will now only run when you execute `python app.py`
    with app.app_context():
        print("--- DATABASE INITIALIZATION ---")
        print(f"Attempting to create database at the following ABSOLUTE path:")
        print(f"==> {app.config['SQLALCHEMY_DATABASE_URI']}")
        db.create_all()
        print("Database tables created successfully.")
        print("-----------------------------")

    app.run(debug=True)
