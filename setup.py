import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cord-client-python",
    version="0.1.3",
    author="Cord Technologies Limited",
    author_email="hello@cord.tech",
    description="Cord Python API Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cord-team/cord-client-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords=["cord"],
    install_requires=[
        "requests",
    ],
)
