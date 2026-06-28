FROM python:3.12-slim

WORKDIR /app

COPY license_keys.py stripe_checkout.py server.py ./

ENV THORPE_LICENSE_SERVER_HOST=0.0.0.0
ENV THORPE_LICENSE_SERVER_PORT=8787
ENV THORPE_LICENSE_SESSION_STORE=/data/checkout_sessions.json

EXPOSE 8787

VOLUME ["/data"]

CMD ["python3", "server.py"]
