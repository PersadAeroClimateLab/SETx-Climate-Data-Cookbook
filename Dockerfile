FROM quay.io/jupyter/base-notebook

COPY . .

USER root
RUN chmod -R 777 notebooks/ src/

USER jovyan
RUN mkdir -p data/
RUN conda env update --name base --file environment.yml