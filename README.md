PyMPCDI
=====

This program provides a bare-bones OpenGL implementation of the 2-D
MPCDI warping specification, using PyOpenGL.  See:

http://www.vesa.org/news/vesa-completes-specifications-for-new-multiple-projector-common-data-interchange-standard-mpcdi/

The input is an mpcdi file using the '2d' profile, and the name of one
region defined within the file.  This program will open a window to
display the contents of the indicated media image (a single frame) as
warped according to the mpcdi file.

This program is intended primarily to serve as a reference
implementation, and not so much to provide a useful function in
itself, though it can be useful to sanity-check mpcdi files.

It is a command-line program.  To use it, open a command-line or
terminal window, change to the source directory, and type the command:

python main.py -m myfile.mpcdi -r region_name

where myfile.mpcdi is the fully-specified path to your mpcdi file, and
region_name is the name of one of the regions in the file.  The
program will open a single window that renders the contents of
region_name.

To list more options, type the command:

python main.py -h

