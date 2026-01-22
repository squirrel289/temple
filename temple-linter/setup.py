from setuptools import setup, find_packages

setup(
    name="temple-linter",
    version="0.1.0",
    description="Linting and diagnostics for templated files. Integrates with template and base format linters.",
    author="Your Name",
    author_email="your@email.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["pygls>=1.0.0"],
    entry_points={
        "console_scripts": ["temple-linter-lsp = temple_linter.lsp_server:main"]
    },
    python_requires=">=3.7",
)
