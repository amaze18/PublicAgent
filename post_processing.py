#postprocessing
from datetime import datetime

# Configure logging for the application
import logging

from utils import call_groq_api

logging.basicConfig(
    filename="app.log",  # Log file name
    filemode='a',  # Append to log file
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',  # Log format
    datefmt='%H:%M:%S',  # Time format in logs
    level=logging.INFO  # Log level: INFO
)

def log_to_supabase(supabase,user_question, bot_response, cit=None, drt=None, rgt=None, personality=None, llm=None,relative_info=None):
    """
    Logs chatbot interaction details to Supabase.

    Args:
        supabase (Client): Supabase client instance for database operations.
        user_question (str): The user's question.
        bot_response (str): Chatbot's response to the user.
        cit (str, optional): Citation or source for any relevant information.
        drt (float, optional): Data retrieval time in milliseconds.
        rgt (float, optional): Response generation time in milliseconds.
        personality (str, optional): Chatbot's personality or profile.
        llm (str, optional): Language model used for generating the response.
        relative_info (str, optional): Additional context used in the response.

    Returns:
        None

    Example:
        Input:
            supabase = <supabase_client>
            user_question = "Who is the Prime Minister of India?"
            bot_response = "The Prime Minister of India is Narendra Modi."
            cit = 143.4
            drt = 45.2
            rgt = 123.4
            personality = "Delhi"
            llm = "meta-llama/llama-3.1-70b-instruct"
            relative_info = "PM of India is Narendra Modi since 2014."

        Output:
            None (Logs the data to Supabase and logs success/failure in the application logs.)
    """
    try:
        # Prepare data to insert
        data = {
            "user_question": user_question,
            "bot_response": bot_response,
            "cit": cit,
            "drt": drt,
            "rgt": rgt,
            "personality": personality,
            "llm": llm,
            "relative_data" : relative_info,
            "timestamp": datetime.utcnow().isoformat()  # ISO format for timestamp
        }

        # Insert into Supabase
        response = supabase.table("chatbot_logs").insert(data).execute()
        logging.info(f"Logged to Supabase: {response}")
    except Exception as e:
        logging.info(f"Error logging to Supabase: {e}")



_all_ =[
  "log_to_supabase"
]

