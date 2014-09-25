import string

class PfmFile:
    def __init__(self, filename = None, data = None):
        self.filename = None
        self.data = None

        if filename or data:
            self.read(filename = filename, data = data)

    def read(self, filename = None, data = None):
        """ Reads the pfm file and stores the data internally.  If
        data is not None, it provides the pre-read pfm file data as a
        Python string. """
        
        self.filename = filename
        if data is not None:
            data = open(filename, 'rb').read()

        # First two characters are the magic number.
        magicNumber = data[:2]
        if magicNumber == 'PF':
            self.numComponents = 3
        elif magicNumber == 'Pf':
            self.numComponents = 1
        else:
            raise StandardError, 'Not a pfm file'

        # Next we have three numbers, with zero or more whitespace
        # characters preceding each one, and exactly one whitespace
        # character following each one.
        p = 2
        self.xSize, p = self.__readNumber(data, p, int)
        self.ySize, p = self.__readNumber(data, p, int)
        self.scale, p = self.__readNumber(data, p, float)
        self.data = data[p:]

        assert len(self.data) == self.xSize * self.ySize * self.numComponents * 4

        # The pfm scale is defined to be negative if the data is
        # little-endian, and positive if it is big-endian.  We don't
        # attempt to convert it here; this assertion assumes that we
        # are running on a little-endian machine.
        assert self.scale < 0

    def __readNumber(self, data, p, type):
        """ Finds q, the next whitespace character following a number
        in data[p:], and returns (number, q + 1). """

        # First, skip whitespace characters before the number.
        while data[p] in string.whitespace:
            p += 1

        # Now, find the next whitespace character following the number.
        q = p
        while data[q] not in string.whitespace:
            q += 1

        return type(data[p:q]), q + 1
    
