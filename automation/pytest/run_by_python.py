import pytest
class MyPlugin:
    def pytest_sessionfinish(self):
        print("*** test run reporting finishing")
pytest.main(["-q",'test_skip.py'], plugins=[MyPlugin()])
