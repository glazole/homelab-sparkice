# Local adaptation of the work Spark/Iceberg stack.
# Verified public image tag; runtime build still needs verification on HP.
FROM apache/spark:3.5.5-scala2.12-java17-python3-ubuntu AS spark-base
USER root
ENV SPARK_HOME=/opt/spark
ENV SPARK_CONF_DIR=/opt/spark/conf
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl python3-venv python3-pip tini \
    && rm -rf /var/lib/apt/lists/*
COPY conf/spark/spark-defaults.conf /opt/spark/conf/spark-defaults.conf
RUN chmod 755 /opt/spark/conf     && chmod 644 /opt/spark/conf/spark-defaults.conf
COPY docker/spark/download-jars.sh /usr/local/bin/download-spark-jars
RUN chmod +x /usr/local/bin/download-spark-jars && /usr/local/bin/download-spark-jars
RUN mkdir -p /tmp/spark-local && chmod 1777 /tmp/spark-local
USER spark

FROM spark-base AS notebook
USER root
RUN python3 -m venv /opt/jupyter-venv
ENV PATH=/opt/jupyter-venv/bin:${PATH}
COPY docker/spark/requirements-notebook.txt /tmp/requirements-notebook.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements-notebook.txt
RUN mkdir -p /home/spark/work /home/spark/.ipython/profile_default/startup \
    && chown -R spark:root /home/spark
COPY spark-ui-startup.py /home/spark/.ipython/profile_default/startup/10-spark-ui.py
ENV HOME=/home/spark
ENV PYSPARK_PYTHON=/opt/jupyter-venv/bin/python
ENV PYSPARK_DRIVER_PYTHON=/opt/jupyter-venv/bin/python
ENV SPARK_HOME=/opt/spark
WORKDIR /home/spark/work
USER spark
