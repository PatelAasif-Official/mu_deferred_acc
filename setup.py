from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in mu_deferred_acc/__init__.py
from mu_deferred_acc import __version__ as version

setup(
	name="mu_deferred_acc",
	version=version,
	description="mu_deferred_acc",
	author="asif patel",
	author_email="patelasif52@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
