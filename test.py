import duckdb
import os

def a(database_subset):
    conn = duckdb.connect(database=':memory:', read_only=False)
    query_result = conn.execute("SELECT Nome_e_Cognome FROM database_subset").fetchdf().reset_index(drop=True)
    return query_result


os.chdir('data')
conn = duckdb.connect(database=':memory:', read_only=False)
t = "1R2176985"
database_subset = conn.execute(f"SELECT * FROM data.csv WHERE Codice = '1R2176985'").fetchdf().reset_index(drop=True)
print(a(database_subset))

