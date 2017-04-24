import builtins
class A:
    def __init__(self,ty):
        self.app=ty
class B:
    def __init__(self,ty):
        self.app=ty
builtins.__dict__['pc1']=A('class a')
builtins.__dict__['pc2']=B('class b')
