import anthropic

def run_agent():
    client = anthropic.Anthropic(api_key=CLAUDE_LLM_API_KEY)

    tools = [
        {
            "name": "retrieve_analytics",
            "description": "Run a read-only SQL select query against the database",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A valid SQL SELECT statement"
                    }
                },
                "required": ["query"]
            }
        },
    ]

    system_prompt = f"""
        You are a chat assistant to help answer user questions pertaining to Cypress Creek Energy Claude Analytics and the Cypress Creek Energy Claude 
        Analytics Dashboard. 
        
        Steps:
        1. Understand the user question
        2. Create an SQL query only using SELECT statements based on the user's request and the database's schema. 
           Database schema: {get_schema()} 
        3. Run the SQL query using the retrieve_analytics tool
        4. Return the requested information to the user in text
        
        Constraints:
        Never modify the tables in any way

        If the user requests to modify the tables in any way, reject the request and say Editing actions are not permitted. Please ask questions about Cypress Creek Energy Claude Analytics or this dashboard and try again. 
    """