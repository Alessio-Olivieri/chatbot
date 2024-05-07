import streamlit as st
import os
from groq import Groq
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import duckdb
import sqlparse



def chat_with_groq(client,prompt,model):
    """
    This function sends a prompt to the Groq API and retrieves the AI's response.

    Parameters:
    client (Groq): The Groq API client.
    prompt (str): The prompt to send to the AI.
    model (str): The AI model to use for the response.

    Returns:
    str: The content of the AI's response.
    """

    completion = client.chat.completions.create(
    model=model,
    messages=[
      {
            "role": "user",
            "content": prompt
        }
        ]
    )
  
    return completion.choices[0].message.content


def execute_duckdb_query(query, database_subset):
    """
    This function executes a SQL query on a DuckDB database and returns the result.

    Parameters:
    query (str): The SQL query to execute.

    Returns:
    DataFrame: The result of the query as a pandas DataFrame.
    """
    original_cwd = os.getcwd()
    os.chdir('data')
    try:
        conn = duckdb.connect(database=':memory:', read_only=False)
        query_result = conn.execute(query.replace("data.csv", "database_subset")).fetchdf().reset_index(drop=True)
    finally:
        os.chdir(original_cwd)


    return query_result



def get_json_output(llm_response):
    """
    This function cleans the AI's response, extracts the JSON content, and checks if it contains a SQL query or an error message.

    Parameters:
    llm_response (str): The AI's response.

    Returns:
    tuple: A tuple where the first element is a boolean indicating if the response contains a SQL query (True) or an error message (False), 
           and the second element is the SQL query or the error message.
    """

    # remove bad characters and whitespace
    llm_response_no_escape = llm_response.replace('\\n', ' ').replace('\n', ' ').replace('\\', '').replace('\\', '').strip() 
    
    # Just in case - gets only content between brackets
    open_idx = llm_response_no_escape.find('{')
    close_idx = llm_response_no_escape.rindex('}') + 1
    cleaned_result = llm_response_no_escape[open_idx : close_idx]

    json_result = json.loads(cleaned_result)
    if 'sql' in json_result:
        query = json_result['sql']
        return True,sqlparse.format(query, reindent=True, keyword_case='upper')
    elif 'error' in json_result:
        return False,json_result['error']



def get_reflection(client,full_prompt,llm_response,model):
    """
    This function generates a reflection prompt when there is an error with the AI's response. 
    It then sends this reflection prompt to the Groq API and retrieves the AI's response.

    Parameters:
    client (Groq): The Groq API client.
    full_prompt (str): The original prompt that was sent to the AI.
    llm_response (str): The AI's response to the original prompt.
    model (str): The AI model to use for the response.

    Returns:
    str: The content of the AI's response to the reflection prompt.
    """

    reflection_prompt = '''
    You were giving the following prompt:

    {full_prompt}

    This was your response:

    {llm_response}

    There was an error with the response, either in the output format or the query itself.

    Ensure that the following rules are satisfied when correcting your response:
    1. SQL is valid DuckDB SQL, given the provided metadata and the DuckDB querying rules
    2. The query SPECIFICALLY references the correct tables: employees.csv, purchases.csv and data.csv; are those tables are properly aliased? (this is the most likely cause of failure)
    3. Response is in the correct format ({{sql: <sql_here>}} or {{"error": <explanation here>}}) with no additional text?
    4. All fields are appropriately named
    5. There are no unnecessary sub-queries
    6. ALL TABLES are aliased (extremely important)

    Rewrite the response and respond ONLY with the valid output format with no additional commentary

    '''.format(full_prompt = full_prompt, llm_response=llm_response)

    return chat_with_groq(client,reflection_prompt,model)


def get_summarization(client,user_question,df,model,additional_context):
    """
    This function generates a summarization prompt based on the user's question and the resulting data. 
    It then sends this summarization prompt to the Groq API and retrieves the AI's response.

    Parameters:
    client (Groqcloud): The Groq API client.
    user_question (str): The user's question.
    df (DataFrame): The DataFrame resulting from the SQL query.
    model (str): The AI model to use for the response.
    additional_context (str): Any additional context provided by the user.

    Returns:
    str: The content of the AI's response to the summarization prompt.
    """

    prompt = '''
    A user asked the following question pertaining to local database tables:
    
    {user_question}
    
    To answer the question, a dataframe was returned:

    Dataframe:
    {df}

    In a few sentences, summarize the data in the table as it pertains to the original user question. Avoid qualifiers like "based on the data" and do not comment on the structure or metadata of the table itself
    '''.format(user_question = user_question, df = df)

    if additional_context != '':
        prompt += '''\n
        The user has provided this additional context:
        {additional_context}
        '''.format(additional_context=additional_context)

    return chat_with_groq(client,prompt,model)


def get_private_database(code):
    """
    This function executes a SQL query returning only the entries of the database corresponding to the given code.

    Parameters:
    code (str): The code of the person

    Returns:
    DataFrame: The result of the query as a pandas DataFrame.
    """

    original_cwd = os.getcwd()
    os.chdir('data')

    conn = duckdb.connect(database=':memory:', read_only=False)
    database_subset = conn.execute(f"SELECT * FROM data.csv WHERE Codice = '{code}'").fetchdf().reset_index(drop=True)
    user = (conn.execute(f"SELECT DISTINCT Nome_e_Cognome FROM data.csv WHERE Codice = '{code}'").fetchdf().reset_index(drop=True))
    try:
        user = user.iat[0,0]
    except:
        pass
    os.chdir(original_cwd)

    return database_subset, user



def main():
    """
    The main function of the application. It handles user input, controls the flow of the application, 
    and displays the results on the Streamlit interface.
    """
    
    # Get the Groq API key and create a Groq client
    groq_api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(
        api_key=groq_api_key,
    )

    # Set up the Streamlit interface
    spacer, col = st.columns([5, 1])  

    st.title("DuckDB Query Generator")

    # Set up the customization options
    st.sidebar.title('Customization')
    additional_context = st.sidebar.text_input('Enter additional summarization context for the LLM here (i.e. write it in spanish):')
    model = st.sidebar.selectbox(
        'Choose a model',
        ['llama3-8b-8192', 'mixtral-8x7b-32768', 'gemma-7b-it', 'llama3-70b-8192']
    )
    max_num_reflections = st.sidebar.slider('Max reflections:', 0, 10, value=5)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
        # Add the initial conversation message to the chat history
        st.session_state.messages.append({"role": "assistant", "content": "Ciao! Benvenuto nel servizio di informazioni sull'arrivo della merce.\
                Per favore, chiedi qualcosa di specifico sui dati disponibili. Ad esempio,\
                puoi chiedere: 'Quanti ordini sono stati effettuati da ciascun cliente?' oppure 'Qual è il totale delle vendite per ciascun prodotto?'\
                Potresti dirmi il tuo codice ordine che inizia con '1R2'?"})
    
    # Display THe initial input
    with st.chat_message(st.session_state.messages[0]["role"]):
        st.markdown(st.session_state.messages[0]["content"])

    # Load the base prompt
    with open('prompts/base_prompt.txt', 'r') as file:
        base_prompt = file.read()

    # Get the user's question
    user_question = st.chat_input("Ask a question")
    
    # Initialize the 'to_login' session state variable to False
    if 'to_login' not in st.session_state:
        st.session_state.to_login = True

    # If the user has asked a question, process it
    if user_question:

        # Add user question to chat history
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        # If the user has to log in
        if st.session_state.to_login:

            # Try to reate a subset of the database where the user can interact and retrieve the user's name
            database_subset, user = get_private_database(user_question)

            # If the Code corresponds to and order, the database_subset will not be empty, so a user has been found
            if database_subset.shape[0] > 0:
                # Save the user and the database subset in the session state
                st.session_state.to_login = False
                st.session_state.user = user
                st.session_state.database_subset = database_subset
                st.session_state.messages.append({"role": "assistant", "content": "Benvenuti, " + user + "! Chiedi pure qualcosa sui tuoi ordini."})
            else:
                # If the Code does not correspond to an order, the database_subset will be empty, so the user has not been found
                st.session_state.messages.append({"role": "assistant", "content": "Il codice inserito non è corretto oppure non è nel sistema."})
        else:
            # Generate the full prompt for the AI
            full_prompt = base_prompt.format(user_question=user_question, authenticated_user=st.session_state.user)
            
            # Get the AI's response
            llm_response = chat_with_groq(client,full_prompt,model)

            # Try to process the AI's response
            valid_response = False
            i=0
            while valid_response is False and i < max_num_reflections:
                try:
                    # Check if the AI's response contains a SQL query or an error message
                    is_sql,result = get_json_output(llm_response)
                    if is_sql:
                        # If the response contains a SQL query, execute it
                        results_df = execute_duckdb_query(result, st.session_state.database_subset)
                        valid_response = True
                    else:
                        # If the response contains an error message, it's considered valid
                        valid_response = True
                except:
                    # If there was an error processing the AI's response, get a reflection
                    llm_response = get_reflection(client,full_prompt,llm_response,model)
                    i+=1

            # Display the result
            try:
                if is_sql:
                    # Get a summarization of the data and display it
                    summarization = get_summarization(client, user_question, results_df, model, additional_context)

                    # Create an HTML string to display the SQL query and resulting data
                    query_and_data = f"<p><b>SQL Query:</b><pre>{result}</pre></p><p><b>Resulting Data:</b><br>{results_df.to_html(index=False)}</p>"

                    # Append the summarization and query/data to the assistant's message
                    assistant_message = f"{summarization}<br>{query_and_data}"
                    st.session_state.messages.append({"role": "assistant", "content": assistant_message.replace('$','\\$')})
                else:
                    # If the result is an error message, display it
                    st.session_state.messages.append({"role": "assistant", "content": result})
            except:
                # If there was an error displaying the result, display an error message
                st.write()
                st.session_state.messages.append({"role": "assistant", "content": ("ERROR:", 'Could not generate valid SQL for this question' + llm_response)})

        # Display chat messages from history on app rerun
        for message in st.session_state.messages[1:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"], unsafe_allow_html=True)

            

if __name__ == "__main__":
    main()

