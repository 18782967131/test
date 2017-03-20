#coding:utf-8
import win32gui
import win32api
import win32con
import win32process
import os
import time
import autopy
path=r'C:\Program Files (x86)\VMware\Infrastructure\Virtual Infrastructure Client\Launcher\VpxClient.exe'
def em_hd(hd):
    #遍历同级句柄
    hd1=win32gui.GetWindow(hd,5)
    while True:
        hd2=win32gui.GetWindow(hd1,2)
        if hd2:
            hd1=hd2
        else:
            break
        print hex(hd2)
def get_hd(hd,t):
    #找同级句柄,t等于序号减1   2确定  6账号  7 密码
    hd_li=[win32gui.GetWindow(hd,5)]   #hd3=win32gui.GetWindow(hd2,5)#找窗口子句柄
    for x in range(0,t):
        hd_li.append(win32gui.FindWindowEx(hd,hd_li[x],None,None))
    return hd_li[-1]
def login_client(path,ip=r'10.11.123.6',user=r'root',password=r'sigma-rt'):
    os.startfile(path)
    time.sleep(1)
    hd=win32gui.FindWindow(None,'VMware vSphere Client')
    while not hd:
        hd=win32gui.FindWindow(None,'VMware vSphere Client')
    ip_hd=win32gui.GetWindow(get_hd(hd,11),5)
    user_hd=get_hd(hd,13)
    pass_hd=get_hd(hd,12)
    login_hd=get_hd(hd,7)
    print hex(hd),hex(user_hd),hex(pass_hd),hex(login_hd)
    win32gui.SendMessage(ip_hd, win32con.WM_SETTEXT, None, ip)
    win32gui.SendMessage(user_hd, win32con.WM_SETTEXT, None, user)
    win32gui.SendMessage(pass_hd, win32con.WM_SETTEXT, None, password)
    win32gui.SendMessage(hd, win32con.WM_COMMAND,1,login_hd)
    hd2=win32gui.FindWindow(None,'{} - vSphere Client'.format(ip))
    while not hd2:
        hd2=win32gui.FindWindow(None,'{} - vSphere Client'.format(ip))
        time.sleep(1)
    time.sleep(5)
    autopy.key.tap(autopy.key.K_RETURN)
    time.sleep(1)
    pos1=find_img_pos(os.path.join(os.path.abspath('.'),r'my_module\img\5.png'))
    autopy.mouse.move(pos1[0],pos1[1])
    autopy.mouse.click(autopy.mouse.LEFT_BUTTON)
    time.sleep(1)
def find_img_pos(path):
    #截屏
    main_screen=autopy.bitmap.capture_screen()
    weixin = autopy.bitmap.Bitmap.open(path)
    pos = main_screen.find_bitmap(weixin)
    if pos:
        return pos[0]+weixin.width/2,pos[1]+weixin.height/2
    else:
        return None
def set_interface4(mode=False):
    pt=os.path.join(os.path.abspath('.'),r'my_module\img\1.png')
    if not mode:
        pt1=os.path.join(os.path.abspath('.'),r'my_module\img\r2.png')
        pos0=find_img_pos(pt1)
        while not pos0:
            pos0=find_img_pos(pt1)
        autopy.mouse.move(pos0[0],pos0[1])
        autopy.mouse.click()
    pos1=find_img_pos(pt)
    while not pos1:
        pos1=find_img_pos(pt)
    autopy.mouse.move(pos1[0],pos1[1])
    autopy.mouse.click(autopy.mouse.RIGHT_BUTTON)
    #输入字串 一个字符相当于按下这个按键
    autopy.key.type_string('E')
    pos2=find_img_pos(os.path.join(os.path.abspath('.'),r'my_module\img\2.png'))
    while not pos2:
        pos2=find_img_pos(os.path.join(os.path.abspath('.'),r'my_module\img\2.png'))
    autopy.mouse.move(pos2[0],pos2[1])
    autopy.mouse.click()
    if mode:
        path=r'my_module\img\3.png'
    else:
        path=r'my_module\img\4.png'
    pos3=find_img_pos(os.path.join(os.path.abspath('.'),path))
    while not pos3:
        pos3=find_img_pos(os.path.join(os.path.abspath('.'),path))
    autopy.mouse.move(pos3[0],pos3[1])
    autopy.mouse.click()
    autopy.key.tap(autopy.key.K_RETURN)
if __name__=='__main__':
    login_client(path)
    set_interface4(True)
    set_interface4()#1.9s
