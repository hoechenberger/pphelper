from __future__ import print_function
import numpy as np
from pphelper import racemodel

# Example data from Ulrich et al., 2007
#
C = {'x': np.array([244, 249, 257, 260, 264, 268, 271, 274, 277, 291]),
     'y': np.array([245, 246, 248, 250, 251, 252, 253, 254, 255, 259, 263, 265, 279, 282, 284, 319]),
     'z': np.array([234, 238, 240, 240, 243, 243, 245, 251, 254, 256, 259, 270, 280])}

results = racemodel.compare_cdfs_from_raw_rts(C['x'], C['y'], C['z'])
print(results)

# Write output to an Excel file?
saveExcel = True
path = 'D:/Temp/Racemodel Results.xlsx'

if saveExcel:
    try:
        results.to_excel(path)
        print('\nExcel file successfully saved to %s.' % path)
    except IOError:
        print('\nCould not save Excel file %s!' % path)
