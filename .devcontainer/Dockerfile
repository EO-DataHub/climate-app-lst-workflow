FROM ubuntu:24.04

# Install dependencies
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:ubuntugis/ubuntugis-unstable && \
    apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    libpq-dev \
    gdal-bin \
    libgdal-dev

# Set GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN python3 -m venv /opt/venv


# Install Python dependencies
COPY ../requirements.txt .
RUN /opt/venv/bin/pip install -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

# Set the entrypoint
ENTRYPOINT ["tail", "-f", "/dev/null"]