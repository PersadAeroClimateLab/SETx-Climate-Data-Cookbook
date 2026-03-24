FROM quay.io/jupyter/base-notebook

COPY . .

RUN conda env update --name base --file environment.yml