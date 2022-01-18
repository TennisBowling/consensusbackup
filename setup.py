from setuptools import setup

setup(
    name='consensusbackup',
    version='0.0.1',
    author='TennisBowling',
    author_email='tennisbowling@tennisbowling.com',
    packages=['consensusbackup'],
    url='https://github.com/TennisBowling/consensusbackup',
    license='LICENSE.md',
    description='A high-availability routing consensus node program',
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    python_requires=">=3.8",
    install_requires=[
        'aiohttp',
        'asyncio',
        'sanic==21.12.1'
    ],
)