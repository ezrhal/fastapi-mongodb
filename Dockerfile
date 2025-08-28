FROM python:3.11-slim

WORKDIR /app

# OS deps and Microsoft repo for msodbcsql18
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl gnupg2 ca-certificates unixodbc unixodbc-dev \
  && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg \
  && echo "deb [arch=amd64,arm64] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update \
  && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 mssql-tools18 \
  && ln -s /opt/mssql-tools18/bin/sqlcmd /usr/bin/sqlcmd || true \
  && ln -s /opt/mssql-tools18/bin/bcp /usr/bin/bcp || true \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--relaod", "--host", "0.0.0.0", "--port", "8080"]
