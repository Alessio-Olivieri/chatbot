import duckdb
import os

def a(database_subset):
    conn = duckdb.connect(database=':memory:', read_only=False)
    query_result = conn.execute("SELECT Nome_e_Cognome FROM database_subset").fetchdf().reset_index(drop=True)
    return query_result


os.chdir('data')
conn = duckdb.connect(database=':memory:', read_only=False)
query_result = conn.execute("SELECT * FROM data.csv AS orders WHERE Spedito = 'SI'").fetchdf().reset_index(drop=True)
print(query_result)