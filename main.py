from MpcdiFile import MpcdiFile
import sys

mpcdi = MpcdiFile(sys.argv[1])

pfm = mpcdi.extractPfmFile('right_warp.pfm')
print pfm.xSize, pfm.ySize, pfm.scale


