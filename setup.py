from setuptools import setup

setup(
    name='examtool',
    version='0.1.0',
    packages=['examtool', 'typst_exam'],
    install_requires=['requests', 'markdown'],
    entry_points={
        'console_scripts': [
            'examtool = examtool:main',
            'typst_exam = typst_exam:main',
        ]
    },
)
