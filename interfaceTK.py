import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.widgets import Slider, CheckButtons
import scan3d
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
from tkinter import ttk
import openDir

class Interface:
    def __init__(self,path):
        #load images
        self.scan = scan3d.Scan3d(path)
        self.pos = [1,1,1]
        self.scan.update(self.pos[0],'xy')
        self.scan.update(self.pos[1],'xz')
        self.scan.update(self.pos[2],'yz')
        
        #set up view controlls
        self.window = Tk()
        frameMain = Frame(self.window)
        frameMain.pack(fill=BOTH,expand=True,padx=10,pady=10)
        
        openButton = Button(frameMain, text="Open", command=self.openDialog)
        openButton.pack(fill=BOTH,expand=True)

        frameSlices = Frame(frameMain)
        frameSlices.pack(fill=BOTH,expand=True,padx=10,pady=10)
        labelSlices = Label(frameSlices,text = "Position")
        labelSlices.pack(fill=BOTH,expand=True)

        self.sliderXY = Scale(frameSlices, from_=0, to=len(self.scan.frames3d[:,0,0])-1, orient=HORIZONTAL,command=self.xy, label="XY")
        self.sliderXY.set(0)
        self.sliderXY.pack(fill="both",expand=True)
        
        self.sliderXZ = Scale(frameSlices, from_=0, to=len(self.scan.frames3d[0,:,0])-1, orient=HORIZONTAL,command=self.xz, label="XZ")
        self.sliderXZ.set(0)
        self.sliderXZ.pack(fill="both",expand=True)
        
        self.sliderYZ = Scale(frameSlices, from_=0, to=len(self.scan.frames3d[0,0,:])-1, orient=HORIZONTAL,command=self.yz, label="YZ")
        self.sliderYZ.set(0)
        self.sliderYZ.pack(fill="both",expand=True)

        frameRange = Frame(frameMain)
        frameRange.pack(fill=BOTH,expand=True,padx=10,pady=10)
        labelRange = Label(frameRange,text = "Value Range")
        labelRange.pack(fill=BOTH,expand=True)

        histFig, histAx = plt.subplots(1,1,figsize=(12,0.5))
        histAx.hist(self.scan.frames3d.flatten(),bins=500,range=(-1000,1000),log=True)
        histAx.get_xaxis().set_visible(False)
        histAx.get_yaxis().set_visible(False)
        histAx.margins(0,tight=True)
        plt.subplots_adjust(left=0,bottom=0,right=1,top=1,wspace=0,hspace=0)
        canvasHist = FigureCanvasTkAgg(histFig,master=frameRange)
        canvasHist.draw()
        histWid = canvasHist.get_tk_widget()
        histWid.pack(fill="both")

        self.sliderMin = Scale(frameRange, from_=-1000, to=1000, orient=HORIZONTAL,command=self.umin, label="Min")
        self.sliderMin.set(-1000)
        self.sliderMin.pack(fill=X,expand=True)

        self.sliderMax = Scale(frameRange, from_=-1000, to=1000, orient=HORIZONTAL,command=self.umax, label="Max")
        self.sliderMax.set(1000)
        self.sliderMax.pack(fill=X,expand=True)

        canvasView = FigureCanvasTkAgg(self.scan.fig,master=frameMain)
        canvasView.draw()
        ViewWid = canvasView.get_tk_widget()
        ViewWid.pack(fill="both",expand=True)

        buttonFrame = Frame(frameMain)
        buttonFrame.pack(fill=BOTH, expand=True)
        checkFlipXY = ttk.Checkbutton(buttonFrame, text="flip xy", command=self.flipXY).grid(row=0,column=0)
        checkFlipXZ = ttk.Checkbutton(buttonFrame, text="flip xz", command=self.flipXZ).grid(row=0,column=1)
        checkFlipYZ = ttk.Checkbutton(buttonFrame, text="flip yz", command=self.flipYZ).grid(row=0,column=2)

        renderMode = StringVar()
        self.comboMode = ttk.Combobox(frameMain,textvariable=renderMode, values=("slice","xray","max","first hit"))
        self.comboMode.bind('<<ComboboxSelected>>',self.changeRender)
        self.comboMode.state(['readonly'])
        self.comboMode.set("slice")
        self.comboMode.pack(expand=True)
        
        self.window.mainloop()

    def openDialog(self):
        self.window.destroy()
        openDir.open_dir()

    def flipXY(self):
        self.scan.xyFlip = not self.scan.xyFlip
        self.scan.update(self.pos[0],'xy')
    def flipXZ(self):
        self.scan.xzFlip = not self.scan.xzFlip
        self.scan.update(self.pos[1],'xz')
    def flipYZ(self):
        self.scan.yzFlip = not self.scan.yzFlip
        self.scan.update(self.pos[2],'yz')

    def changeRender(self,event):
        label = self.comboMode.get()
        self.scan.mode = label        
        self.scan.update(self.pos[0],'xy')
        self.scan.update(self.pos[1],'xz')
        self.scan.update(self.pos[2],'yz')
        self.scan.updatermax(int(self.sliderMax.get()))
        self.scan.updatermin(int(self.sliderMin.get()))
    
    def xy(self,z):
        self.pos[0] = z
        self.scan.update(z,'xy')
    def xz(self,y):
        self.pos[1] = y
        self.scan.update(y,'xz')
    def yz(self,x):
        self.pos[2] = x
        self.scan.update(x,'yz')
    
    def umax(self,maxr):
        self.scan.updatermax(int(maxr))
        if (self.scan.mode == "xray" or self.scan.mode == "max" or self.scan.mode == "first hit"):
            self.scan.update(self.pos[0],'xy')
            self.scan.update(self.pos[1],'xz')
            self.scan.update(self.pos[2],'yz')
    def umin(self,minr):
        self.scan.updatermin(int(minr))
        if (self.scan.mode == "xray" or self.scan.mode == "max" or self.scan.mode == "first hit"):
            self.scan.update(self.pos[0],'xy')
            self.scan.update(self.pos[1],'xz')
            self.scan.update(self.pos[2],'yz')
