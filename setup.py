import sys
if sys.platform == "win32":
    from distutils.core import setup
    import py2exe

    setup(windows=[{"script":"NovalIDE.py","icon_resources":[(1, u"noval.ico")]}],
          options = { "py2exe":{"dll_excludes":["MSVCP90.dll"]}},
            data_files=[("noval/tool/bmp_source", ["noval/tool/bmp_source/noval.ico"]),
                ("noval/tool/data",["noval/tool/data/tips.txt"])],)
elif sys.platform.find('linux') != -1:
    from distutils.core import setup
    from setuptools import find_packages

    install_requires = ['wxpython','pyyaml',"watchdog","chardet","pyperclip"]
    setup(name='NovalIDE',
            version='1.0.0',
            description='''noval ide is a cross platform code editor''',
            author='wukan',
            author_email='wekay102200@sohu.com',
            url='https://github.com/noval102200/Noval.git',
            license='Genetalks',
            packages=find_packages(),
            install_requires=install_requires,
            zip_safe=False,
            test_suite='noval.tests',
            package_data={'noval': [
                        'tool/bmp_source/*',
                        'tool/data/*',
            ]},
            classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy'
            ],
            entry_points="""
            [console_scripts]
            NovalIDE = noval.noval:main
            """
)

