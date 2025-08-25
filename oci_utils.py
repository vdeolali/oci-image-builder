import oci
import configparser
from oci.core import ComputeManagementClient

def get_oci_profiles(config_file):
    """
    Parses the OCI config file to get a list of available profiles.
    """
    profiles = []
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        profiles = config.sections()
        if not profiles and 'DEFAULT' in config:
            profiles.append('DEFAULT')
    except Exception as e:
        print(f"Could not parse OCI config file at '{config_file}': {e}")
    return profiles

def get_oci_images(compartment_id, config_file, profile_name):
    """
    Fetches a list of Oracle Linux images from OCI.
    """
    try:
        config = oci.config.from_file(file_location=config_file, profile_name=profile_name)
        compute_client = oci.core.ComputeClient(config)
        images = compute_client.list_images(
            compartment_id=compartment_id, 
            operating_system='Oracle Linux',
            sort_by='DISPLAYNAME', 
            lifecycle_state='AVAILABLE'
        ).data
        return sorted([(image.id, image.display_name) for image in images], key=lambda x: x[1])
    except Exception as e:
        print(f"Error in get_oci_images: {e}")
        return []

# --- THIS IS THE CORRECTED FUNCTION NAME ---
def get_available_shapes(compartment_id, config_file, profile_name):
    """
    Fetches all available shapes. This is a placeholder and should ideally
    be replaced with a function that gets shapes compatible with an image.
    For now, it lists all shapes.
    """
    try:
        config = oci.config.from_file(file_location=config_file, profile_name=profile_name)
        compute_client = oci.core.ComputeClient(config)
        
        # This lists all available shapes in the compartment.
        # Note: This is a simplified approach. A more advanced implementation
        # would filter shapes based on the selected base image.
        shapes = compute_client.list_shapes(
            compartment_id=compartment_id
        ).data
        
        return sorted([(shape.shape, shape.shape) for shape in shapes])
        
    except oci.exceptions.ServiceError as e:
        print(f"OCI API Error fetching shapes: {e.message}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred fetching shapes: {e}")
        return []

