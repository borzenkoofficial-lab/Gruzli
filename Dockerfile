FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings pyyaml httpx
COPY nexum_core ./nexum_core
COPY configs ./configs
COPY data ./data
EXPOSE 8000
CMD ["uvicorn","nexum_core.api.app:app","--host","0.0.0.0","--port","8000"]
