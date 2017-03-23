import tushare as ts
#'601212'
import time
from tkinter import *
from tkinter import messagebox,filedialog,colorchooser
def get_gp(code):
	#return
	#name pri_open  high low price buy1 sale1
	df = ts.get_realtime_quotes(code)
	li_index=[0,1,4,5,3,6,7]
	li_rpr=[]
	for x in li_index:
		li_rpr.append(df.values[0][x])
	return li_rpr
master = Tk()
master.title("bg")                     
master.geometry('400x400+420+250')                
#master.resizable(width=False, height=False)
Label(master,text="name").grid(row=0,column=1,columnspan=1,padx=5,pady=5)
Label(master,text="open").grid(row=0,column=2,columnspan=1,padx=5,pady=5)
Label(master,text="high").grid(row=0,column=3,columnspan=1,padx=5,pady=5)
Label(master,text="low").grid(row=0,column=4,columnspan=1,padx=5,pady=5)
Label(master,text="price").grid(row=0,column=5,columnspan=1,padx=5,pady=5)
Label(master,text="buy").grid(row=0,column=6,columnspan=1,padx=5,pady=5)
Label(master,text="sale").grid(row=0,column=7,columnspan=1,padx=5,pady=5)
name=StringVar()
name.set('junchen')
t=Text(master)
t.grid(row=1,column=1,columnspan=20,padx=5,pady=5)
state=StringVar()
state.set('begin')
t.insert(1.0,'12 445 6656')
def auto_get():
	def counter(i):
		if i > 0:
			t.delete(0.0,END)
			t.insert(1.0,'  '.join(get_gp('601212'))+'\n')
			t.insert(2.0,'  '.join(get_gp('000651'))+'\n')
			t.insert(3.0,str(i)+'\n')
			t.update()
			t.after(1000, counter, i-1)
		else:
			goBtn.config(state=NORMAL)
	goBtn.config(state=DISABLED)
	counter(60*60*60)
goBtn=Button(master,textvariable=state,compound=CENTER,command=auto_get)
goBtn.grid(row=3,column=4,columnspan=1,padx=5,pady=5)
master.mainloop()