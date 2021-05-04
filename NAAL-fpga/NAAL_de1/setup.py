from setuptools import find_packages, setup

setup(
    name='nengo_de1',
    packages=find_packages(),
    version='0.2.1',
    author='Applied Brain Research',
    description='NengoFPGA Interface for DE1',
    author_email='info@appliedbrainresearch.com',
    install_requires=["numpy>=1.13.0"],
)
