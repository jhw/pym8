"""
### overview

- the whole setuptools/setup.py dance is a total shitshow

### packages

- ideally packages should be auto- installed from specification of a project root, but no such luck
- it appears setup() wants you to use `packages=setuptools.find_packages()` but this seems completely broken
- it's quite common to find a target project supposedly installed by pip that is completely empty
- instead, implement `filter_packages` and use that
- setup() `packages` arg clearly needs a list of packages

### non- python files

- non- python files are not installed by default
- seems to be whole load of conflicting advice on this one
- correct answer is here
- https://stackoverflow.com/a/57932258/124179

```
setup_requires=['setuptools_scm'],
include_package_data=True
```

- :/

### dependencies

- mercifully stuff in requirements.txt seems to be installed by default
- at least if you stick to vanilla pip declarations
- I haven't tried 
  - pip versions (I think these can be assumed to work)
  - pip sub- packages (moto; don't think these work)
  - git packages (think some modifications required here; try pareto2/setup.py from 0.6.x
"""

import setuptools, os

with open("README.md", "r") as fh:
    long_description=fh.read()

with open('requirements.txt', 'r') as f:
    requirements=f.read().splitlines()

def filter_packages(root):
    def filter_packages(root, packages):
        packages.append(root.replace("/", "."))
        for path in os.listdir(root):
            if path=="__pycache__":
                continue
            newpath="%s/%s" % (root, path)
            if os.path.isdir(newpath):
                filter_packages(newpath, packages)
    packages=[]
    filter_packages(root, packages)
    return packages
    
setuptools.setup(
    name="pym8",
    version="0.1.0",
    author="jhw",
    author_email="justin.worrall@gmail.com",
    description="A Python package for the parsing of Dirtywave M8 files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jhw/pym8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # packages=setuptools.find_packages(),
    packages=filter_packages("pym8"),
    install_requires=requirements,
    # - https://stackoverflow.com/a/57932258/124179
    setup_requires=['setuptools_scm'],
    include_package_data=True
)
