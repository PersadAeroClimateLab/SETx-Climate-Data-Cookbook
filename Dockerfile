FROM quay.io/jupyter/base-notebook

COPY notebooks/ notebooks/
COPY src/ src/
COPY assets assets/
COPY environment.yml .

USER root
RUN chmod -R 777 notebooks/ src/ assets/ environment.yml

USER jovyan
RUN mkdir -p data/ && \
    conda env update --name base --file environment.yml && \
    conda clean -afy && \
    jupyter lab build && \
    rm -rf /home/jovyan/.cache