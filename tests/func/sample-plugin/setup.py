from setuptools import setup

setup(
    name='temboard-sample-plugin',
    version='1.0',
    py_modules=['temboard_sample_plugin'],
    entry_points={
        "temboard.plugins": [
            "extsample = temboard_sample_plugin:SamplePlugin"
        ],
    },
)
