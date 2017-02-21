import win32gui
from pprint import pprint
 
def gbk2utf8(s):
    return s.decode('gbk').encode('utf-8')
 
def show_window_attr(hWnd):
    '''
    ��ʾ���ڵ�����
    :return:
    '''
    if not hWnd:
        return
    #����ϵͳĬ��title��gb2312�ı���
    title = win32gui.GetWindowText(hWnd)
    title = gbk2utf8(title)
    clsname = win32gui.GetClassName(hWnd)
 
    print '���ھ��:%s ' % (hWnd)
    print '���ڱ���:%s' % (title)
    print '��������:%s' % (clsname)
    print ''
 
def show_windows(hWndList):
    for h in hWndList:
        show_window_attr(h)
 
def demo_top_windows():
    '''
    ��ʾ����г����еĶ�������
    :return:
    '''
    hWndList = []
    #arg1 �ص����� arg2 ����б�
    win32gui.EnumWindows( lambda hWnd,param:param.append(hWnd), hWndList)
    show_windows(hWndList)
 
    return hWndList
 
def demo_child_windows(parent):
    '''
    ��ʾ����г����е��Ӵ���
    :return:
    '''
    if not parent:
        return
    hWndChildList = []
    #arg1 ����� arg2 �ص����� arg3 ����б�
    win32gui.EnumChildWindows(parent, lambda hWnd, param: param.append(hWnd),  hWndChildList)
    show_windows(hWndChildList)
    return hWndChildList
demo_top_windows()
