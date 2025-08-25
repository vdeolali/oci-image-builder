from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

class ImageBlueprintForm(FlaskForm):
    cloud_provider = StringField('Cloud Provider', default='OCI', render_kw={'readonly': True})
    oci_profile = SelectField('OCI Profile', validators=[DataRequired()])
    base_image = SelectField('Base Image', validators=[DataRequired()])
    
    # --- ADD THESE THREE FIELDS ---
    shape = SelectField('Instance Shape', validators=[DataRequired()])
    ocpus = StringField('OCPUs', default='1', validators=[Optional()])
    memory_in_gbs = StringField('Memory (GB)', default='16', validators=[Optional()])
    
    packages = TextAreaField('Packages to Install (one per line)', validators=[DataRequired()])
    submit = SubmitField('Build Image')

