"""AgriGuide backend package.

This explicit package marker lets hosting platforms import ``backend.app.main``
when the repository root is the deployment root, while local development can
still run ``uvicorn app.main:app`` from the backend directory.
"""
