# db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from urllib.parse import quote_plus

driver = "ODBC Driver 18 for SQL Server"
server = "192.168.101.52"
database = "spms"
username = "web"
password = "z$,41997644GYTP"

# put the DRIVER=... in the query string; it must be URL-encoded
query = {
    "driver": driver,
    "Encrypt": "yes",
    "TrustServerCertificate": "yes",  # dev only; prefer proper certs in prod
}

query_str = "&".join(f"{k}={quote_plus(v)}" for k, v in query.items())

ASYNC_DB_URL = (
    f"mssql+aioodbc://{username}:{quote_plus(password)}@{server}/{database}?{query_str}"
)
# e.g. mssql+aioodbc://sa:YourStrong%21Passw0rd@localhost,1433/mydb?driver=ODBC%20Driver%2018%20for%20SQL%20Server&Encrypt=yes&TrustServerCertificate=yes

engine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def spms_session():
    async with AsyncSessionLocal() as session:
        yield session
