ARG PYTHON_VERSION=3.7
FROM reg.nic.cz/python/tox:${PYTHON_VERSION}
RUN apt-get --yes update \
 && apt-get install --yes --no-install-recommends \
    gettext \
    git \
    libomniorb4-2 \
    python3-setuptools \
    # libpython is needed by omniorb
    libpython3.7 \
    ssh \
 && rm -rf /var/lib/apt/lists/*
