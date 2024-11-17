from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="picamera2-webstream",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Flask-based web streaming solution for Raspberry Pi cameras using PiCamera2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/picamera2-webstream",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Multimedia :: Video :: Capture",
    ],
    python_requires=">=3.7",
    install_requires=[
        "flask>=2.0.0",
        "picamera2>=0.3.9",
        "opencv-python>=4.5.0",
        "numpy>=1.19.0",
    ],
)