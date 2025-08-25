import os
import json
import subprocess
import oci  # Import the OCI library
from models import db, ImageBuild
from flask import current_app

def generate_packer_template(build_request):
    """
    Generates the Packer template and injects authentication details directly.
    """
    packages_to_install = build_request.packages.splitlines()
    install_command = f"sudo yum install -y {' '.join(packages_to_install)}"

    # --- START OF MODIFICATION: Explicitly load auth details ---
    # Load the specified OCI profile using the Python SDK
    oci_config = oci.config.from_file(
        file_location=current_app.config['OCI_CONFIG_FILE'],
        profile_name=build_request.oci_profile
    )

    # Create a dictionary with the exact authentication keys Packer needs
    auth_details = {
        "tenancy_ocid": oci_config.get("tenancy"),
        "user_ocid": oci_config.get("user"),
        "key_file": oci_config.get("key_file"),
        "fingerprint": oci_config.get("fingerprint"),
    }
    # --- END OF MODIFICATION ---

    source_block = {
        # Inject the explicit authentication details into the source block
        **auth_details,

        # The rest of the configuration is the same
        "availability_domain": current_app.config['OCI_AVAILABILITY_DOMAIN'],
        "compartment_ocid": current_app.config['OCI_COMPARTMENT_OCID'],
        "subnet_ocid": current_app.config['OCI_SUBNET_OCID'],
        "base_image_ocid": build_request.base_image,
        "image_name": f"custom-image-build-{build_request.id}-{build_request.created_at.strftime('%Y%m%d%H%M%S')}",
        "shape": build_request.shape,
        "ssh_username": "opc"
    }

    if 'Flex' in build_request.shape:
        source_block["shape_config"] = {
            "ocpus": build_request.ocpus,
            "memory_in_gbs": build_request.memory_in_gbs
        }

    packer_config = {
        "packer": {"required_plugins": {"oracle": {"version": "~> 1", "source": "github.com/hashicorp/oracle"}}},
        "source": {"oracle-oci": {"oci-base-image": source_block}},
        "build": {
            "sources": ["source.oracle-oci.oci-base-image"],
            "provisioner": [{"shell": {"inline": ["sudo yum update -y", install_command]}}]
        }
    }
    return packer_config


def run_packer_build(app, build_id):
    """
    Runs the Packer build process.
    """
    with app.app_context():
        build_request = ImageBuild.query.get(build_id)
        if not build_request:
            print("Error: Build not found.")
            return

        build_request.status = 'Building'
        db.session.commit()
        
        packer_config = generate_packer_template(build_request)
        config_filename = f"build-{build_id}.pkr.json"
        
        with open(config_filename, "w") as f:
            json.dump(packer_config, f, indent=4) # Use indent 4 for readability

        packer_output_log = ""
        build_succeeded = False

        try:
            print(f"Starting Packer build with explicit auth for OCI Profile: {build_request.oci_profile}...")
            
            # We no longer need to set OCI_PROFILE as auth is in the JSON
            build_process = subprocess.Popen(
                ["packer", "build", "-force", config_filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
            )

            for line in iter(build_process.stdout.readline, ''):
                print(line.strip())
                packer_output_log += line
            build_process.wait()

            if build_process.returncode == 0:
                build_succeeded = True
            else:
                print("Packer build failed.")
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            packer_output_log += f"\nERROR: {error_msg}"
        finally:
            build_request = ImageBuild.query.get(build_id)
            build_request.status = 'Completed' if build_succeeded else 'Failed'
            build_request.packer_output = packer_output_log
            db.session.commit()
            if os.path.exists(config_filename):
                os.remove(config_filename)
            print(f"Cleaned up {config_filename}.")

