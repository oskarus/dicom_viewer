import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, CheckButtons
from matplotlib.colors import Normalize
import numpy as np
import sys
import os
from joblib import Parallel, delayed
import math
from skimage.morphology import flood_fill
import time
import multiprocessing
from multiprocessing.managers import BaseManager
from itertools import product
import dicom
sys.setrecursionlimit(512*512)

class Scan3d:
    def __init__(self,path):
        #render mode
        self.mode = "slice"
        #open files 
        frames = []
        files = os.listdir(os.path.abspath(path))
        self.dim = [1,1,1]#voxel dimentions
        for fname in files:
            f = open(os.path.join(path,fname),"rb")
            dicomFile = dicom.DicomFile(f)
            location = dicomFile.location
            pixeldata = dicomFile.pixeldata
            rs = dicomFile.rescaleSlope
            ri = dicomFile.rescaleIntercept
            self.dim = dicomFile.voxelDimentions
            frames.append((float(location),pixeldata))
        frames.sort()
        frames2 = []
        for i in frames:
            frames2.append(i[1])
        #value display range parameters
        self.vmin = -1000
        self.vmax = 1000
        #flip along depth axis parameters
        self.xyFlip = False
        self.xzFlip = False
        self.yzFlip = False
        #conver values to hounsfield scale
        self.frames3d = np.stack(frames2)
        rescaleIntercept = np.ones_like(self.frames3d)
        rescaleIntercept = np.multiply(rescaleIntercept,ri)
        self.frames3d = np.multiply(self.frames3d,rs)
        self.frames3d = self.frames3d + rescaleIntercept
        #flip the whole volume along z axis
        self.frames3d = np.flip(self.frames3d,axis=0)
        #matplotlib plots, key=plane string
        self.fig, self.axes = plt.subplots(1,3,figsize=(12,4))
        self.slices = dict()
        self.slices["xy"] = self.axes[0].imshow(self.frames3d[0,:,:],interpolation='none',aspect = self.dim[2]/self.dim[1], norm = Normalize(vmin=self.vmin,vmax=self.vmax))
        self.slices["xz"] = self.axes[1].imshow(np.flipud(self.frames3d[:,0,:]),interpolation='none', aspect = self.dim[0]/self.dim[1], norm = Normalize(vmin=self.vmin,vmax=self.vmax))
        self.slices["yz"] = self.axes[2].imshow(np.rot90(self.frames3d[:,:,0],2),interpolation='none', aspect = self.dim[0]/self.dim[2], norm = Normalize(vmin=self.vmin,vmax=self.vmax))
    #maximum value of display range update
    def updatermin(self,a):
        nyz = self.slices["yz"].norm
        nxy = self.slices["xy"].norm
        nxz = self.slices["xz"].norm
        
        if nxy.vmax > a:
            nxy.vmin = a
        else:
            nxy.vmin = nxy.vmax
        nyz = nxy
        nxz = nxy
        self.vmin = nxy.vmin

        if self.mode == "first hit": 
            self.slices["xy"].norm.vmin = 0
            self.slices["xz"].norm.vmin = 0
            self.slices["yz"].norm.vmin = 0
            self.slices["xy"].norm.vmax = len(self.frames3d[:,0,0])
            self.slices["xz"].norm.vmax = len(self.frames3d[0,0,:])
            self.slices["yz"].norm.vmax = len(self.frames3d[0,:,0])
        else:
            self.slices["xy"].norm = nxy
            self.slices["xz"].norm = nxz
            self.slices["yz"].norm = nyz
        
        self.fig.canvas.draw_idle()
    #minumum value of display range update
    def updatermax(self,a):
        nyz = self.slices["yz"].norm
        nxy = self.slices["xy"].norm
        nxz = self.slices["xz"].norm
        
        if nxy.vmin < a:
            nxy.vmax = a
        else:
            nxy.vmax = nxy.vmin
        nyz = nxy
        nxz = nxy
        self.vmax = nxy.vmax
        
        if self.mode == "first hit":
            self.slices["xy"].norm.vmin = 0
            self.slices["xz"].norm.vmin = 0
            self.slices["yz"].norm.vmin = 0
            self.slices["xy"].norm.vmax = len(self.frames3d[:,0,0])
            self.slices["xz"].norm.vmax = len(self.frames3d[0,0,:])
            self.slices["yz"].norm.vmax = len(self.frames3d[0,:,0])
        else: 
            self.slices["xy"].norm = nxy
            self.slices["xz"].norm = nxz
            self.slices["yz"].norm = nyz
        
        self.fig.canvas.draw_idle()
    #alternative render mode
    def xray(self,data,plane):
        if plane == "xy":
            out = np.mean(data,axis=0)
        elif plane == "yz":
            out = np.mean(data,axis=1)
        elif plane == "xz":
            out = np.mean(data,axis=2)
        return out
    #alternative render mode
    def max(self,data,plane):
        if plane == "xy":
            out = data.max(axis=0)
        elif plane == "yz":
            out = data.max(axis=1)
        elif plane == "xz":
            out = data.max(axis=2)
        return out
    #alternative render mode
    def first(self,data,plane):
        if plane == "xy":
            out = np.argmax(data>self.vmin,axis=0)
        elif plane == "yz":
            out = np.argmax(data>self.vmin,axis=1)
        elif plane == "xz":
            out = np.argmax(data>self.vmin,axis=2)
        return out
    #main display function
    def update(self,a,plane):
        picture = self.slices[plane].norm
        if plane == "xy":
            if self.mode == "slice":
                data = self.frames3d[int(a),:,:]
            else:
                if int(a) == 0:
                    temp = self.frames3d[0:1,:,:]
                else:
                    temp = self.frames3d[0:int(a),:,:]
                if self.xyFlip:
                    temp = np.flip(temp,axis=0)           
                if self.mode == "xray":
                    data = self.xray(temp,plane)
                elif self.mode == "first hit":
                    pad = np.tile(-1000,(10,np.shape(self.frames3d)[1],np.shape(self.frames3d)[2]))
                    temp = np.concatenate((pad,temp),axis=0)
                    data = self.first(temp,plane)
                elif self.mode == "max":
                    data = self.max(temp,plane)
        elif plane == "yz":
            if self.mode == "slice":
                data = self.frames3d[:,int(a),:]
            else:
                if int(a) == 0:
                    temp = self.frames3d[:,0:1,:]
                else:
                    temp = self.frames3d[:,0:int(a),:]
                if self.yzFlip:
                    temp = np.flip(temp,axis=1)
                if self.mode == "xray":
                    data = self.xray(temp,plane)
                elif self.mode == "first hit":
                    pad = np.tile(-1000,(np.shape(self.frames3d)[0],10,np.shape(self.frames3d)[2]))
                    temp = np.concatenate((pad,temp),axis=1)
                    data = self.first(temp,plane)
                elif self.mode == "max":
                    data = self.max(temp,plane)
        elif plane == "xz":
            if self.mode == "slice":
                data = self.frames3d[:,:,int(a)]
            else:
                if int(a) == 0:
                    temp = self.frames3d[:,:,0:1]
                else:
                    temp = self.frames3d[:,:,0:int(a)]
                if self.xzFlip:
                    temp = np.flip(temp,axis=2)
                if self.mode == "xray":
                    data = self.xray(temp,plane)
                elif self.mode == "first hit":
                    pad = np.tile(-1000,(np.shape(self.frames3d)[0],np.shape(self.frames3d)[1],10))
                    temp = np.concatenate((pad,temp),axis=2)
                    data = self.first(temp,plane)
                elif self.mode == "max":
                    data = self.max(temp,plane)
        self.slices[plane].set_data(data)
        self.fig.canvas.draw_idle()
