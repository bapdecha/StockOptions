FROM postgres

ENV PGDATA=/var/lib/postgresql/data/postgresql.conf

WORKDIR /home/postgres/

RUN mkdir postgres_data/

RUN chown postgres postgres_data/

USER postgres

RUN initdb -D postgres_data -U bapdecha

CMD ["postgres", "-D", "postgres_data/"]