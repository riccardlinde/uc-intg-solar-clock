FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core fonts-roboto fonts-liberation && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY driver.json .
COPY uc_intg_analog_clock ./uc_intg_analog_clock
ENV UC_INTEGRATION_INTERFACE=0.0.0.0
ENV UC_INTEGRATION_HTTP_PORT=9095
CMD ["python", "-m", "uc_intg_analog_clock.driver"]
