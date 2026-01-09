# pull official base image
FROM python:3.11-alpine

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 

# Install uv
RUN pip install uv

# set work directory
WORKDIR /app

# Copy uv project files first (for better caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv's project management
RUN uv sync --frozen --no-dev

COPY . .

WORKDIR /app/src

# run entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]