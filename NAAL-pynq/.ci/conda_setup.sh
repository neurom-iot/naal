#!/usr/bin/env bash

conda config --set always_yes yes --set changeps1 no

# Exit if the de1-docs env already exists
if conda info --envs | grep de1-docs > /dev/null; then
    return 0
fi

# Otherwise, set it up
conda update --quiet conda
conda create --quiet --name de1-docs python=3.6
source activate de1-docs
conda install --quiet cython jupyter matplotlib mkl numpy scipy
pip install flake8 ghp-import nengo_sphinx_theme "sphinx>1.7" nbsphinx numpydoc
source deactivate
# Also set up git for pushing to Github
git config --global user.email "gl@appliedbrainresearch.com"
git config --global user.name "Applied Brain Research"
