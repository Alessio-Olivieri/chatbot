## Overview
This repository contains a Streamlit-based chatbot application designed for managing customer orders in an e-commerce setting. The chatbot interacts with users to provide order updates and uses the **Groq API** for Natural Language Processing (NLP) tasks, such as generating responses, handling errors, and summarizing data. It also integrates with **DuckDB** for executing SQL queries and managing order data.

### Features:
- Provides real-time updates about customer orders using a simple order code (starting with "1R2").
- Handles SQL queries and responses through a combination of Groq API and DuckDB.
- Supports summarizing the order status based on specific user queries.
- Customizable interaction model selection.
- Ability to handle API reflection for error responses.
- Integrates gender detection for personalized messaging.

## Technologies Used:
- **Streamlit**: For the frontend web interface.
- **Groq API**: For generating AI-based responses.
- **DuckDB**: Lightweight SQL execution engine.
- **SentenceTransformer**: For embedding and similarity matching (future usage).
- **Gender Guesser**: To personalize responses based on user’s name.

## How to Run

### Prerequisites:
- Python 3.7+
- An active **Groq API** key.

### Setup:

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3. Create a `secrets.toml` file in the `.streamlit` folder, and add your **Groq API key**:
    ```toml
    [secrets]
    GROQ_API_KEY = "your_groq_api_key"
    ```

4. Ensure your data is available in the `data/` directory with the correct structure. The expected CSV files include:
   - `employees.csv`
   - `purchases.csv`
   - `data.csv`

### Running the App:

To start the Streamlit app, run the following command in your terminal:
```bash
streamlit run app.py
```

### Usage:

Once the application is running, users can interact with the chatbot:
1. Provide an order code (starting with '1R2').
2. The bot will respond with the order status based on data retrieved from the DuckDB queries.
3. You can customize responses, context, and model selection from the sidebar.

## File Structure:
- `app.py`: The main application script that handles the Streamlit interface and logic.
- `prompts/base_prompt.txt`: Base prompt template used for generating AI responses.
- `data/`: Directory containing CSV files used in DuckDB queries.

## Key Functions:

- `chat_with_groq(client, prompt, model)`: Sends a prompt to the Groq API and retrieves a response.
- `execute_duckdb_query(query, database_subset)`: Executes SQL queries on a DuckDB database.
- `get_json_output(llm_response)`: Cleans and parses JSON responses from Groq's API.
- `get_reflection(client, full_prompt, llm_response, model)`: Handles error corrections and reflections for invalid SQL or output.
- `get_summarization(client, user_question, df, model, additional_context, user)`: Generates summaries from query results.
- `get_private_database(code)`: Extracts order-specific data from the DuckDB for a given order code.

## Error Handling:
- Handles various errors such as:
  - Invalid Groq API key (401).
  - Rate limit exceeded (429).
  - Internal server error (500).
  - Service unavailable (503).

## Customization:
- You can adjust the model used for Groq's NLP responses via the sidebar.
- Additional context for responses can be added using a text input field.
- The number of error reflections can be configured using a slider.

## License
This project is licensed under the MIT License.

---

