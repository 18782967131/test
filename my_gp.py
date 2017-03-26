import tushare as ts
from tkinter import *
from tkinter import messagebox,filedialog,colorchooser
from tkinter import scrolledtext
import sys  
import os  
import struct  
import time  
import win32con  
from win32api import *
import threading
# -*- encoding:utf-8 -*-  
##############################
#
# 程序名：python桌面托盘气泡
# 文件名：clsBubble.py
# 功能 ：实现桌面托盘气泡提示功能
# modify：by adengou 2016.1.4
# program:python3.4.4
# 适用  ：windowsXP -windows10
#
##############################
import sys  
import os  
import struct  
import time  
import win32con  
  
from win32api import *  
# Try and use XP features, so we get alpha-blending etc.  
try:  
  from winxpgui import *  
except ImportError:  
  from win32gui import *  
  
  
class PyNOTIFYICONDATA:  
  _struct_format = (  
    "I" # DWORD cbSize; 结构大小(字节)  
    "I" # HWND hWnd; 处理消息的窗口的句柄  
    "I" # UINT uID; 唯一的标识符  
    "I" # UINT uFlags;  
    "I" # UINT uCallbackMessage; 处理消息的窗口接收的消息  
    "I" # HICON hIcon; 托盘图标句柄  
    "128s" # TCHAR szTip[128]; 提示文本  
    "I" # DWORD dwState; 托盘图标状态  
    "I" # DWORD dwStateMask; 状态掩码  
    "256s" # TCHAR szInfo[256]; 气泡提示文本  
    "I" # union {  
        #   UINT  uTimeout; 气球提示消失时间(毫秒)  
        #   UINT  uVersion; 版本(0 for V4, 3 for V5)  
        # } DUMMYUNIONNAME;  
    "64s" #    TCHAR szInfoTitle[64]; 气球提示标题  
    "I" # DWORD dwInfoFlags; 气球提示图标  
  )  
  _struct = struct.Struct(_struct_format)  
  
  hWnd = 0  
  uID = 0  
  uFlags = 0  
  uCallbackMessage = 0  
  hIcon = 0  
  szTip = ''  
  dwState = 0  
  dwStateMask = 0  
  szInfo = ''  
  uTimeoutOrVersion = 0  
  szInfoTitle = ''  
  dwInfoFlags = 0  
  
  def pack(self):  
    return self._struct.pack(  
     self._struct.size,  
      self.hWnd,  
      self.uID,  
      self.uFlags,  
      self.uCallbackMessage,  
      self.hIcon,  
      self.szTip.encode("gbk"),  
      self.dwState,  
      self.dwStateMask,  
      self.szInfo.encode("gbk"),  
      self.uTimeoutOrVersion,  
      self.szInfoTitle.encode("gbk"),  
      self.dwInfoFlags
    )
  
  def __setattr__(self, name, value):  
    # avoid wrong field names  
    if not hasattr(self, name):  
      raise (NameError, name)  
    self.__dict__[name] = value  
  
class MainWindow:  
  def __init__(self):
    #初始化变量
    self.title =""
    self.msg =""
    self.duration=10#延时5秒
    self.hwnd =None
    self.hinst =None
    self.regOk = False
    #self.creWind()
 
  
  def creWind(self):
     # Register the Window class.
    wc = WNDCLASS()  
    self.hinst = wc.hInstance = GetModuleHandle(None)  
    wc.lpszClassName = "PythonTaskbarDemo" # 字符串只要有值即可，下面3处也一样  
    wc.lpfnWndProc = { win32con.WM_DESTROY: self.OnDestroy } # could also specify a wndproc.   
    classAtom = RegisterClass(wc)
    # Create the Window.  
    style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU  
    self.hwnd = CreateWindow(classAtom, "Taskbar Demo", style,  
      0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,  
      0, 0, self.hinst, None  
    )
    UpdateWindow(self.hwnd)
  #
  def startBubble(self,title, msg, duration=3):
    
    if(self.hwnd==None):
      self.creWind()
    self.title =title
    self.msg=msg
    self.duration=duration
    
    iconPathName = os.path.abspath(os.path.join(sys.prefix, os.getcwd()+"\\pyc.ico"))  
    icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE  
    try:  
      hicon = LoadImage(self.hinst, iconPathName, win32con.IMAGE_ICON, 0, 0, icon_flags)  
    except:  
      hicon = LoadIcon(0, win32con.IDI_APPLICATION)  
    flags = NIF_ICON | NIF_MESSAGE | NIF_TIP  
    nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "Balloon  tooltip demo")  
    try:
      Shell_NotifyIcon(NIM_ADD, nid)
    except:
      self.hwnd==None
    self.show_balloon(self.title, self.msg)
    
    time.sleep(self.duration)
    #ReleaseDC(self.hwnd,wc)
    #DeleteDC(wc)
    try:
      DestroyWindow(self.hwnd)
      self.hwnd==None
    except:
      return None
    
  
  def show_balloon(self, title, msg):  
    # For this message I can't use the win32gui structure because  
    # it doesn't declare the new, required fields
  
    nid = PyNOTIFYICONDATA()  
    nid.hWnd = self.hwnd  
    nid.uFlags = NIF_INFO  
  
    # type of balloon and text are random  
    #nid.dwInfoFlags = NIIF_INFO  
    nid.szInfo = msg[:64]
    nid.szInfoTitle = title[:256]  
  
    # Call the Windows function, not the wrapped one  
    from ctypes import windll  
    Shell_NotifyIcon = windll.shell32.Shell_NotifyIconA  
    Shell_NotifyIcon(NIM_MODIFY, nid.pack())  
  
  def OnDestroy(self, hwnd, msg, wparam, lparam):  
    nid = (self.hwnd, 0)  
    Shell_NotifyIcon(NIM_DELETE, nid)  
    PostQuitMessage(0) # Terminate the app.  
def get_gp(code):
	#return
	#name open  high low price buy1 sale1
	try:
		df = ts.get_realtime_quotes(code)
	except:
		time.sleep(2)
		df = ts.get_realtime_quotes(code)
	li_index=[0,1,4,5,3,6,7]
	li_rpr=[]
	for x in li_index:
		li_rpr.append(df.values[0][x])
	return li_rpr
msgTitle =u"this is bubble alert:"
bubble =MainWindow()
#####################################################
#                     tkinter                       #
#####################################################
master = Tk()
master.title("bg")                     
master.geometry('400x400+420+250')                
#master.resizable(width=False, height=False)
Label(master,text="name").grid(row=0,column=0,padx=2, pady=5)
Label(master,text="open").grid(row=0,column=1,padx=2, pady=5)
Label(master,text="high").grid(row=0,column=2,padx=2, pady=5)
Label(master,text="low").grid(row=0,column=3,padx=2, pady=5)
Label(master,text="price").grid(row=0,column=4,padx=2, pady=5)
Label(master,text="buy").grid(row=0,column=5,padx=2, pady=5)
Label(master,text="sale").grid(row=0,column=6,padx=2, pady=5)
name=StringVar()
name.set('junchen')
t=scrolledtext.ScrolledText(master)
t.grid(row=1,column=0,columnspan=16,padx=2, pady=5)
state=StringVar()
state.set('begin')
def auto_get():
	def counter(i):
		if i > 0:	
			t.delete(0.0,END)
			my_gp=['601212','000885','002808','000403','000651','002166']
			for x in my_gp:
				datas=get_gp(x)
				t.insert(my_gp.index(x)+1.0,'  '.join(datas)+'\n')
			t.update()
			t.after(1000, counter, i-1)
		else:
			goBtn.config(state=NORMAL)
	goBtn.config(state=DISABLED)
	counter(60*60*60)
goBtn=Button(master,textvariable=state,compound=CENTER,command=auto_get)
goBtn.grid(row=3)
#提示涨幅
def alert_(code,my_price,bubble):
	li={'601212':0,'002166':0}
	x=code
	while True:
		datas=get_gp(code)
		open=float(datas[1])
		price=float(datas[3])
		if li[x]==0:
			li[x]=open
		if price-li[x]>0 and (price-li[x])/li[x]>0.02:
			li[x]=price
			msgTitle=datas[0]
			msgContent='myprice:'+str(my_price)+'open:'+datas[1]+'price:'+datas[3]+'more than 0.02%,total {rate:}'.format(rate=(price-open)/open)
			bubble.startBubble(msgTitle,msgContent)	
		if price-li[x]<0 and abs((price-li[x])/li[x])>0.02:
			li[x]=price
			msgTitle=datas[0]
			msgContent='myprice:'+str(my_price)+'open:'+datas[1]+'price:'+datas[3]+'less than 0.02%,total {rate:}'.format(rate=(price-open)/open)
			bubble.startBubble(msgTitle,msgContent)
		time.sleep(5)
threads = []
t1 = threading.Thread(target=alert_,args=('601212',16.13,bubble))
t2 = threading.Thread(target=alert_,args=('002166',16.13,bubble))
threads.append(t1)
threads.append(t2)
for th in threads:
	th.start()
master.mainloop()