"""
Editra Buisness Model Library: FileTypeChecker

Helper class for checking what kind of a content a file contains.

"""

__all__ = [ 'FileTypeChecker', ]

#-----------------------------------------------------------------------------#
# Imports
import os
import types

#-----------------------------------------------------------------------------#

class FileTypeChecker(object):
    """File type checker and recognizer"""
    TXTCHARS = ''.join(map(chr, [7, 8, 9, 10, 12, 13, 27] + range(0x20, 0x100)))
    ALLBYTES = ''.join(map(chr, range(256)))

    def __init__(self, preread=4096):
        """Create the FileTypeChecker
        @keyword preread: number of bytes to read for checking file type

        """
        super(FileTypeChecker, self).__init__()

        # Attributes
        self._preread = preread

    @staticmethod
    def _GetHandle(fname):
        """Get a file handle for reading
        @param fname: filename
        @return: file object or None

        """
        try:
            handle = open(fname, 'rb')
        except:
            handle = None
        return handle

    def IsBinary(self, fname):
        """Is the file made up of binary data
        @param fname: filename to check
        @return: bool

        """
        handle = self._GetHandle(fname)
        if handle is not None:
            bytes = handle.read(self._preread)
            handle.close()
            return self.IsBinaryBytes(bytes)
        else:
            return False

    def IsBinaryBytes(self, bytes):
        """Check if the given string is composed of binary bytes
        @param bytes: string

        """
        nontext = bytes.translate(FileTypeChecker.ALLBYTES,
                                  FileTypeChecker.TXTCHARS)
        return bool(nontext)

    def IsReadableText(self, fname):
        """Is the given path readable as text. Will return True if the
        file is accessable by current user and is plain text.
        @param fname: filename
        @return: bool

        """
        f_ok = False
        if os.access(fname, os.R_OK):
            f_ok = not self.IsBinary(fname)
        return f_ok


    def IsUnicode(self,txt):
        """Is the given string a unicode string
        @param txt: object
        @return: bool

        """
        return isinstance(txt, types.UnicodeType)


if __name__ == "__main__":
    
    file_name = r'D:\env\Noval\NovalIDE_Setup.exe'
    
    print FileTypeChecker().IsBinary(file_name)
    print FileTypeChecker().IsReadableText(file_name)