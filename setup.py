from setuptools import find_packages, setup

setup(
    name="ivus-tools",
    version="0.1.0",
    packages=find_packages(),
    py_modules=[
        "dicom_to_mp4",
        "dicom_to_png",
        "png_to_mp4",
        "extract_metadata",
        "batch_convert",
    ],
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.26.0",
        "opencv-python>=4.10.0",
        "pydicom>=3.0.0",
        "pillow>=10.0.0",
        "tqdm>=4.66.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "dicom-to-mp4=dicom_to_mp4:cli",
            "dicom-to-png=dicom_to_png:cli",
            "png-to-mp4=png_to_mp4:cli",
            "ivus-metadata=extract_metadata:cli",
            "ivus-batch-convert=batch_convert:cli",
        ]
    },
)
