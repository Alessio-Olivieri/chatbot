import duckdb
import os

def a(database_subset):
    conn = duckdb.connect(database=':memory:', read_only=False)
    query_result = conn.execute("SELECT Nome_e_Cognome FROM database_subset").fetchdf().reset_index(drop=True)
    return query_result


os.chdir('data')
conn = duckdb.connect(database=':memory:', read_only=False)
query_result = conn.execute("SELECT Stato FROM data.csv AS orders WHERE Codice = '1R2432605'").fetchdf().reset_index(drop=True)
print(query_result)

