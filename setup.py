from setuptools import setup, find_packages

setup(
    name='deepflow',
    version='0.1',
    packages=find_packages(include=['deepflow', 'deepflow.*']),
    package_data={
        'deepflow': [
            'input_files/**/*',
            'input_files/*'
                     ],
    },
    install_requires=[
        'dpgen',
        'dpdata',
        'numpy',
        'matplotlib',
        'seaborn',
        'pandas',
        'statsmodels'
    ],
    entry_points={
        'console_scripts': [
            'deepflow=deepflow.deepflow:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
