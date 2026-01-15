from setuptools import setup, Extension
import pybind11
import os

# Define the C++ extension
cpp_args = ['-std=c++11', '-O3']

ext_modules = [
    Extension(
        'cpp_pathfinder',
        sources=['cpp/bindings.cpp'],
        include_dirs=[pybind11.get_include()],
        language='c++',
        extra_compile_args=cpp_args,
    ),
]

setup(
    name='cpp_pathfinder',
    version='0.0.1',
    description='Fast C++ Pathfinding Extension for PathPilot',
    ext_modules=ext_modules,
)
