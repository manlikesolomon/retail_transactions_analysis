FROM apache/airflow:3.0.2

# Switch to airflow user (default user for Airflow image)
USER airflow

# Copy requirements and install packages
COPY --chown=airflow:root requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt