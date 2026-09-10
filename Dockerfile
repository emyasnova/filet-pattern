FROM node:22.14.0-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST_DIR=/app/frontend/dist \
    PORT=8000
WORKDIR /app/backend
COPY backend/ ./
RUN pip install --no-cache-dir . && \
    groupadd --system app && useradd --system --gid app --home-dir /app app
COPY --from=frontend-build /build/frontend/dist /app/frontend/dist
COPY docker/start.sh /app/start.sh
RUN chmod 0555 /app/start.sh && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["/app/start.sh"]
