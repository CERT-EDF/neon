# =============================================================================
# FUSION DIRECTIVES
# =============================================================================
# fusion:image=cert-edf/neon-be-ct
# fusion:package=edf-fusion
# fusion:package=edf-neon-core
# fusion:package=edf-neon-server
# =============================================================================
# PRODUCTION IMAGE
# =============================================================================
FROM ubuntu:24.04
# ------------------------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------------------------
#
# ------------------------------------------------------------------------------
# NEON CONTENT TYPE ANALYZER
# ------------------------------------------------------------------------------
RUN apt update && \
    apt install --yes ent file nano python3 python3-venv && \
    python3 -m venv /venv && \
    /venv/bin/python -m pip install uv && \
    /venv/bin/uv pip install --python /venv/bin/python magika && \
    mkdir -p /analyzer/ct && \
    ln -s /usr/bin/ent /analyzer/ct/ent && \
    ln -s /usr/bin/file /analyzer/ct/file && \
    ln -s /venv/bin/magika /analyzer/ct/magika
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
