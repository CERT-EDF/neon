# ------------------------------------------------------------------------------
# IMAGE
# ------------------------------------------------------------------------------
FROM ubuntu:24.04
# ------------------------------------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
# COPY PRE-BUILT PACKAGES (OPTIONAL)
# -----------------------------------------------------------------------------
#COPY pkg /pkg
# ------------------------------------------------------------------------------
# NEON CONTENT TYPE ANALYZER
# ------------------------------------------------------------------------------
RUN apt update && \
    apt install --yes ent file nano python3 python3-venv && \
    python3 -m venv /venv && \
    /venv/bin/python -m pip install uv && \
    /venv/bin/uv pip install --python /venv/bin/python edf-neon-server magika && \
    mkdir -p /analyzer/ct && \
    ln -s /usr/bin/ent /analyzer/ct/ent && \
    ln -s /usr/bin/file /analyzer/ct/file && \
    ln -s /venv/bin/magika /analyzer/ct/magika
# ------------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------------
COPY analyzer.py /analyzer.py
COPY --chmod=755 docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
