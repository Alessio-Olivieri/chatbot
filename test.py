import duckdb
import os


os.chdir('data')
conn = duckdb.connect(database=':memory:', read_only=False)
query_result = conn.execute("SELECT 'Nome e Cognome' FROM data.csv").fetchdf().reset_index(drop=True)

print(query_result)