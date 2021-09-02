from interfaceTK import Interface
from tkinter import filedialog
from tkinter import *
#filedialog functionality
def open_dir(): 
    root = Tk()
    root.withdraw()
    root.directory = filedialog.askdirectory()
    path = root.directory
    root.destroy()
    Interface(path)
