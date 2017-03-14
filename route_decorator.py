#类装饰器注册与调用
class App():
	def __init__(self):
		print('init class')
		self.fn={}
	def register(self,name):
		def inner(fun):
			self.fn[name]=fun
			print(self.fn)
		return inner
	def call_main(self,name):
		if name in self.fn.keys():
			return self.fn[name]()
		else:
			return '403 error'
app=App()
@app.register('/')
def main_page():
	return 'this is main page'
@app.register('/next')
def next_page():
	return 'this is next main page'
print(app.call_main('/next'))


#函数装饰器
import time
import functools
def log(text):
	def dec(fun):
		#防止运行改变now函数名字，不加now.__name__改为inner
		#@functools.wraps(fun)
		def inner(*arg,**kw):
			print('call now:%s'%fun.__name__)
			fun()
		return inner
	print(text)
	return dec
#三层嵌套
@log('this is text')
def now():
	print(time.time())
#dec(now)()
now(1,2,3,a=1,n=3)
print(now.__name__)