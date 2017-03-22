class A():
    def __init__(self):
        print("step2:init")
        self.a = 1

    def __new__(cls):
        print("step1:new")
        return super().__new__(cls)

    def __del__(self):
        #_del__是对象的销毁器。它并非实现了语句 del x (因此该语句不等
        #同于 x.__del__())。而是定义了当对象被垃圾回收时的行为。 
        print("call del")

    def __str__(self):
        print("call __str__")
        return "class A str"

    def __repr__(self):
        print("call __repr__")
        return "class A repr"

    def __unicode__(self):
        print("call __unicode__")
        return "class A unicode"

    def __nozero__(self):
        print("call __nozero__")
        return 1

    def __len__(self):
        print("call __len__")
        return 1
    #定以后callable(instance) True
    def __call__(self, *args):
        print("call __call__")
