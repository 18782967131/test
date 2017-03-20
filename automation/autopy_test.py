#coding:utf-8
import autopy
import time
time.sleep(5)
def find_img_pos(path):
    #截屏
    main_screen=autopy.bitmap.capture_screen()
    weixin = autopy.bitmap.Bitmap.open(path)
    pos = main_screen.find_bitmap(weixin)
    if pos:
        return pos[0]+weixin.height/2,pos[1]+weixin.width/2
    else:
        return None
pos=find_img_pos('tt.png') 
autopy.mouse.move(pos[0],pos[1])
#mouse.RIGHT_BUTTON mouse.CENTER_BUTTON mouse.LEFT_BUTTON
#autopy.mouse.click(autopy.mouse.RIGHT_BUTTON)
#autopy.mouse.click()

#输入字符
autopy.key.type_string('Lhhhhhh')
