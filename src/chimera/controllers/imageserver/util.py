
from chimera.core.exceptions import ChimeraException

class ImageServerException(ChimeraException):
    pass

class InvalidFitsImageException(ImageServerException):
    pass
