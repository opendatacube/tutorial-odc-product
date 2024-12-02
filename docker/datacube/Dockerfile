# Use an official OSgeo runtime as a parent image
FROM ghcr.io/osgeo/gdal:ubuntu-full-3.10.0

ARG V_PG=16
ARG V_PGIS=16-postgis-3

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
# Update and install Ubuntu packages

USER root
RUN apt-get update -y \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --allow-change-held-packages --fix-missing --no-install-recommends \
        git libpq-dev \
        python3-dev python3-pip python3-venv virtualenv \
        build-essential \
        postgresql-client-${V_PG} \
        sudo make graphviz \
        tini \
    && apt-get clean

# Install Open Data Cube in venv
COPY requirements.txt /requirements.txt
COPY constraints.txt /constraints.txt
RUN virtualenv /env
# Set the locale, this is required for some of the Python packages
ENV PYENV=/env \
    GDAL_CONFIG=/usr/bin/gdal-config \
    LC_ALL=C.UTF-8

RUN . /env/bin/activate && python3 -m pip --disable-pip-version-check install --no-cache-dir -r requirements.txt -c constraints.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8888

ENTRYPOINT ["/entrypoint.sh"]
USER ubuntu
# HEALTHCHECK documentation: https://docs.docker.com/engine/reference/builder/#healthcheck
# This healtcheck works well for `lab`, `notebook`, `nbclassic`, `server` and `retro` jupyter commands
# https://github.com/jupyter/docker-stacks/issues/915#issuecomment-1068528799
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=3 \
    CMD /etc/jupyter/docker_healthcheck.py || exit 1

WORKDIR /home/ubuntu
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"]