from distutils.core import setup
setup(name='ntf_log',
    version='1.0',                    # 包名
    include_package_data=True,       #自动打包文件夹内所有数据
    packages = ['ntf_log'],           #要打包的项目文件夹
    # 如果要上传到PyPI，则添加以下信息
    # author = "Me",
    # author_email = "me@example.com",
    # description = "This is an Example Package",
    # license = "MIT",
    # keywords = "hello world example examples",
    # url = "http://example.com/HelloWorld/",  
    )