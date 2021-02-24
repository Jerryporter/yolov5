# from tkinter import *
# from tkinter import ttk
# from PIL import tk
import detect as dt
# def calculate(*args):
#     try:
#         value = float(feet.get())
#         meters.set(int(0.3048 * value * 10000.0 + 0.5)/10000.0)
#     except ValueError:
#         pass
#
# root = Tk()
# root.title("Feet to Meters")
#
# mainframe = ttk.Frame(root, padding="3 3 12 12")
# mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
# root.columnconfigure(0, weight=1)
# root.rowconfigure(0, weight=1)
#
# feet = StringVar()
# feet_entry = ttk.Entry(mainframe, width=7, textvariable=feet)
# feet_entry.grid(column=2, row=1, sticky=(W, E))
#
# meters = StringVar()
# ttk.Label(mainframe, textvariable=meters).grid(column=2, row=2, sticky=(W, E))
#
# ttk.Button(mainframe, text="Calculate", command=calculate).grid(column=3, row=3, sticky=W)
#
# ttk.Label(mainframe, text="feet").grid(column=3, row=1, sticky=W)
# ttk.Label(mainframe, text="is equivalent to").grid(column=1, row=2, sticky=E)
# ttk.Label(mainframe, text="meters").grid(column=3, row=2, sticky=W)
# photo=PhotoImage(file='C:/project/python/yolov5/data/images/bus.jpg')
# ttk.Label(image=photo).grid(colume=4,row=4,sticky=W)
# for child in mainframe.winfo_children():
#     child.grid_configure(padx=5, pady=5)
#
# feet_entry.focus()
# root.bind("<Return>", calculate)
#
#
# root.mainloop()

asdf=[1,2,3,4]
for i in range(len(asdf)):
    print(i)