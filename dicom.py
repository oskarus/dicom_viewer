import numpy as np
import re

class DicomDataElement:
    def __init__(self,inFile):
        #if none then eof
        vrs = ['OB','OW','SQ','UN']
        dt32 = np.dtype(np.uint32)
        dt16 = np.dtype(np.uint16)

        groupNum = np.frombuffer(inFile.read(2), dtype=dt16)
        if len(groupNum) == 0:
            self.eof = True
            return
        elementNum = np.frombuffer(inFile.read(2), dtype=dt16)[0]
        self.valueRepresentation = inFile.read(2).decode('UTF-8')
        self.valueLen = 0
        if self.valueRepresentation in vrs:
            #padding
            inFile.read(2)
            #data 32bit
            self.valueLen = np.frombuffer(inFile.read(4), dtype=dt32)[0]
        else:
            #data 16bit
            self.valueLen = np.frombuffer(inFile.read(2), dtype=dt16)[0]
        self.value = inFile.read(self.valueLen)
        self.tag = (groupNum,elementNum)
        self.eof = False
class DicomFile:
    def __init__(self,file):
        preamble = file.read(128)
        prefix = file.read(4)
        eof = False
        self.voxelDimentions = [1,1,1]#z, x, y
        while eof == False: 
            de = DicomDataElement(file)
            if de.eof:
                if not hasattr(self,'pixeldata') or not hasattr(self,'location'):
                    raise Exception("File corrupted or not a dicom file")
                if not hasattr(self,'rescaleSlope') or not hasattr(self,'rescaleIntercept'):
                    raise Exception("No rescaleIntercept or rescaleSlope, cannot rescale data to hounsfield scale")
                eof = True
                break
            if de.tag == (int('7FE0',16),int('10',16)):
                self.pixeldata = np.reshape(np.frombuffer(de.value, dtype=np.int16),(self.rows,self.cols))
            if de.tag == (int('28',16),int('10',16)):
                self.rows = np.frombuffer(de.value, dtype=np.uint16)[0]
            if de.tag == (int('28',16),int('11',16)):
                self.cols = np.frombuffer(de.value, dtype=np.uint16)[0]    
            if de.tag == (int('28',16),int('1053',16)):
                self.rescaleSlope = float(de.value.decode('UTF-8'))
            if de.tag == (int('28',16),int('1052',16)):
                self.rescaleIntercept = float(de.value.decode('UTF-8'))
            if de.tag == (int('20',16),int('1041',16)):
                self.location = de.value.decode('UTF-8')
            if de.tag == (int('18',16),int('50',16)):
                self.voxelDimentions[0] = float(de.value.decode('UTF-8'))
            if de.tag == (int('28',16),int('30',16)):
                val = re.split(r'/|\\',(de.value.decode('UTF-8')))
                self.voxelDimentions[2] = float(val[0])
                self.voxelDimentions[1] = float(val[-1])
