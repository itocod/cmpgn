from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class AnyPasswordValidator:
    def validate(self, password, user=None):
        # No specific validation, any password is accepted
        pass

    def get_help_text(self):
        return _("Your password can be any length and may contain any characters.")
