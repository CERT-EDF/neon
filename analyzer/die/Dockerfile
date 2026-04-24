# =============================================================================
# FUSION DIRECTIVES
# =============================================================================
# fusion:image=cert-edf/neon-be-die
# fusion:package=edf-fusion
# fusion:package=edf-neon-core
# fusion:package=edf-neon-server
# =============================================================================
# PRODUCTION IMAGE
# =============================================================================
FROM ubuntu:24.04
# -----------------------------------------------------------------------------
# ENVIRONMENT
# -----------------------------------------------------------------------------
ENV DEB_URL=https://github.com/horsicq/DIE-engine/releases/download/3.21/die_3.21_Ubuntu_24.04_amd64.deb
# -----------------------------------------------------------------------------
# NEON CONTENT TYPE ANALYZER
# -----------------------------------------------------------------------------
RUN apt update && \
    apt install --yes curl nano python3 python3-venv && \
    python3 -m venv /venv && \
    /venv/bin/python -m pip install uv && \
    curl -L -o ./die.deb "${DEB_URL}" && \
    apt install --yes ./die.deb && \
    apt remove --yes curl && \
    rm ./die.deb && \
    mkdir -p /analyzer/die && \
    ln -s /usr/bin/diec /analyzer/die/diec
# -----------------------------------------------------------------------------
# SETUP FUSION PACKAGES (PROD)
# -----------------------------------------------------------------------------
RUN /venv/bin/uv pip install --python /venv/bin/python edf-neon-server
# -----------------------------------------------------------------------------
# SETUP FUSION PACKAGES (DEV)
# -----------------------------------------------------------------------------
#COPY pkg /pkg
#RUN /venv/bin/uv pip install --python /venv/bin/python --pre --find-links /pkg edf-neon-server
# -----------------------------------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------------------------------
COPY analyzer.py /analyzer.py
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
