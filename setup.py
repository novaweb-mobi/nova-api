import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nova_api",
    version="1.0a1",
    author="Mateus Berardo & Fábio Trevizolo",
    author_email="mateust@novaweb.mobi, fabiots@novaweb.mobi",
    description="A package to accelerate REST API development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/novaweb-mobi/nova-api",
    packages=[
        'nova_api',
    ],
    install_requires=[
        'mysql-connector',
        'flask',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)

