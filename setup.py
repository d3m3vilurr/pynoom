try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='pynoom',
      version='0.0.1',
      url='https://github.com/d3m3vilurr/pynoom',
      author='Sunguk Lee',
      author_email='d3m3vilurr@gmail.com',
      py_modules=['pynoom'],
      install_requires=['requests', 'html5lib'],
      license='MIT')
