#coding:utf-8
class test():
    def __init__(self):
        print 'init'
    #静态方法，类和实例调用
    @staticmethod
    def say():
        print 'i am static function'
    #类方法，通过类或它的实例来调用的方法,方法的第一个参数都是类对象而不是实例对象
    @classmethod
    def say_cls(cls):
        print 'i am method for',cls.__name__
    #实例调用,self实例对象
    def say_self(self):
        print 'i am method for',self.__dict__
class test2(test):
    pass
p=test()
test.say()
p.say()

test_i=test()
test2_i=test2()

test.say_cls()
test_i.say_cls()
test2.say_cls()
test2_i.say_cls()

test_i.say_self()
test2_i.say_self()
