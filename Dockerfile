FROM quay.io/jupyter/base-notebook

ARG NB_USER
ARG NB_UID
ENV USER=${NB_USER}
ENV HOME=/home/${NB_USER}

ENV DOCKER_STACKS_JUPYTER_CMD=notebook

COPY environment.yml ${HOME}/
RUN conda env update --name base --file ${HOME}/environment.yml && \
    conda clean -afy

COPY src/ ${HOME}/src/
COPY assets/ ${HOME}/assets/
COPY notebooks/ ${HOME}/notebooks/

RUN mkdir -p ${HOME}/.jupyter/custom
COPY custom.css ${HOME}/.jupyter/custom/custom.css
COPY custom.js ${HOME}/.jupyter/custom/custom.js

RUN mkdir -p ${HOME}/data/
COPY data/download_links.txt ${HOME}/data/
RUN wget -c -P data/ -i data/download_links.txt

USER root
RUN chmod -R 777 ${HOME}/notebooks/ ${HOME}/src/ ${HOME}/assets/ && \
    chown -R ${NB_UID}:${NB_UID} ${HOME}
USER ${NB_USER}