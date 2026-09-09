FROM ubuntu@sha256:c664f8f86ed5a386b0a340d981b8f81714e21a8b9c73f658c4bea56aa179d54a
ENV DEBIAN_FRONTEND=noninteractive
COPY packages.txt packages.lock.json verify_packages.py /opt/build-inputs/
RUN apt-get update && xargs -r apt-get install -y --no-install-recommends < /opt/build-inputs/packages.txt && python3 /opt/build-inputs/verify_packages.py /opt/build-inputs/packages.lock.json && rm -rf /var/lib/apt/lists/*
COPY emulator.bundle revision.txt /opt/build-inputs/
RUN git clone /opt/build-inputs/emulator.bundle /opt/emulator && cd /opt/emulator && git checkout --detach "$(cat /opt/build-inputs/revision.txt)" && test "$(git rev-parse HEAD)" = "$(cat /opt/build-inputs/revision.txt)"
WORKDIR /opt/emulator
RUN ./dev/emu fetch --locked && ./dev/emu build && python3 scripts/build_audio_candidate.py --output .runtime/container-audio && python3 scripts/prepare_audio_monitor.py --install .runtime/container-audio/installation.json --output .runtime/container-audio-tools
RUN useradd --create-home --uid 1000 emulator && mkdir -p /data /opt/emulator/.runtime/sessions && chown emulator:emulator /data && chmod 1777 /opt/emulator/.runtime/sessions && git config --system --add safe.directory /opt/emulator
ENV HOME=/home/emulator PYTHONDONTWRITEBYTECODE=1
USER emulator
EXPOSE 8765
STOPSIGNAL SIGTERM
ENTRYPOINT ["python3", "/opt/emulator/scripts/container/entrypoint.py"]
