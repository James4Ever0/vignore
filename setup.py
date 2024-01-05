from setuptools import setup

setup(
    name="vignore",
    version="1.0.3",
    packages=["vignore"],
    description="Visualize ignored files and directories by rules.",
    url="https://github.com/james4ever0/vignore",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "numpy",
        "rich",
        "textual",
        "jinja2",
        "beartype",
        "aiofiles",
        "asyncio",
    ],
    entry_points="""
        [console_scripts]
        vignore=vignore.cli:main
    """,
)
