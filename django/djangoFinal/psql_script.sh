docker run -d \
  --name formationdjango \
  -e POSTGRES_PASSWORD=secret \
  -p 5433:5432 \
  postgres:17-alpine
sleep 5
docker exec formationdjango psql -U postgres -c "CREATE USER djangouser WITH PASSWORD 'secret' CREATEDB;"
docker exec formationdjango psql -U postgres -c "CREATE DATABASE formationdjango OWNER djangouser;"