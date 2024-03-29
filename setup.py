import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="NovaAPI",
    version="{{VERSION}}",
    license='MIT',
    author="Mateus Berardo & Fábio Trevizolo",
    author_email="mateust@novaweb.mobi, fabiots@novaweb.mobi",
    description="A package to accelerate REST API development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/novaweb-mobi/nova-api",
    packages=setuptools.find_packages(exclude=("*tests",)),
    install_requires=[
        'mysql-connector',
        'flask',
        'flask-cors',
        'connexion[swagger-ui]',
        'python-jose>=3.2.0',
        'makefun'
    ],
    extras_require={
        'postgresql': ['psycopg2-binary'],
        'mongo': ['pymongo >= 3.12, < 4.0', 'python-dateutil']
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': ['generate_nova_api=nova_api:generate_api']
    }
)

