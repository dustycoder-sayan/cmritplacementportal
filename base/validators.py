import requests
import re
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _

def validate_google_drive_link(value):
    """Custom validator to check if the provided Google Drive link is valid and accessible."""
    url_validator = URLValidator()
    
    try:
        url_validator(value)
    except ValidationError:
        raise ValidationError(_('Invalid URL format'))

    # Check if the URL is a Google Drive link
    if 'drive.google.com' not in value:
        raise ValidationError(_('Not a Google Drive link'))

    # Check if the link is accessible by making a request to the Google Drive API
    try:
        response = requests.get(value)
        response.raise_for_status()
    except requests.RequestException:
        raise ValidationError(_('Failed to access the Google Drive link'))

def validate_usn(value):
    pattern = r'^1CR20[A-Za-z]{2}\d{3}$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Invalid USN Format'),
            code='invalid_usn'
        )
