# ------------------------------------------------------------------------------
# IMAGE
# ------------------------------------------------------------------------------
FROM ubuntu:24.04
# ------------------------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------------------------
ENV DEB_URL=https://github.com/horsicq/DIE-engine/releases/download/3.10/die_3.10_Ubuntu_24.04_amd64.deb
# -----------------------------------------------------------------------------
# COPY PRE-BUILT PACKAGES (OPTIONAL)
# -----------------------------------------------------------------------------
#COPY pkg /pkg
# ------------------------------------------------------------------------------
# NEON CONTENT TYPE ANALYZER
# ------------------------------------------------------------------------------
RUN apt update && \
    apt install --yes curl nano python3 python3-venv && \
    python3 -m venv /venv && \
    /venv/bin/python -m pip install uv && \
    /venv/bin/uv pip install --python /venv/bin/python edf-neon-server && \
    curl -L -o ./die_3.10_Ubuntu_24.04_amd64.deb "${DEB_URL}" && \
    apt install --yes ./die_3.10_Ubuntu_24.04_amd64.deb && \
    apt remove --yes curl && \
    rm ./die_3.10_Ubuntu_24.04_amd64.deb && \
    mkdir -p /analyzer/die && \
    ln -s /usr/bin/diec /analyzer/die/diec
# ------------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------------
COPY analyzer.py /analyzer.py
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
