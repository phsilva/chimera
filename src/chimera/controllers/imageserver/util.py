
from chimera.core.exceptions import ChimeraException, ObjectNotFoundException, ClassLoaderException
from chimera.core.path import ChimeraPath

def getImageServer(manager):

    try:
        toReturn = manager.getProxy('/ImageServer/0')
    except ObjectNotFoundException:
        toReturn = manager.addLocation('/ImageServer/imageserver', [ChimeraPath.controllers()])

    if not toReturn:
        raise ClassLoaderException('Unable to create or find an ImageServer')

    return toReturn

class ImageServerException(ChimeraException):
    pass

class InvalidFitsImageException(ImageServerException):
    pass
