from setuptools import setup, find_packages

setup(
    name="CRED_VOICE-ASSISTANT",
    version="0.1.0",
    description="Voice-first Agentic AI for Indian Government Scheme Assistance",
    author="Tushar7012",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
    "fastapi",
    "uvicorn",
    "vosk",
    "edge-tts"
],
    python_requires=">=3.9",
)
