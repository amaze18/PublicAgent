
import redis
from fastapi import FastAPI,File,UploadFile,Form,BackgroundTasks
from pydantic import BaseModel,validator
from typing_extensions import Annotated
from typing import Union
import json
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client, Client

# Add asyncio
import asyncio

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

from utils import call_groq_api  

from model import get_response_by_bot
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=3)

# Initialize FastAPI application
app = FastAPI()


# Add CORS middleware to allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,  # Allow credentials (e.g., cookies, headers)
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all HTTP headers
)


# Supabase connection details
SUPABASE_URL = os.getenv("SUPABASE_URL")  # Supabase project URL from environment variable
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Supabase API key from environment variable

# Configure logging for the application
import logging
logging.basicConfig(
    filename="app.log",  # Log file name
    filemode='a',  # Append to log file
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',  # Log format
    datefmt='%H:%M:%S',  # Time format in logs
    level=logging.INFO  # Log level: INFO
)

# Create a Supabase client using project URL and API key
# Create singleton for Supabase client
class SupabaseClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = create_client(SUPABASE_URL, SUPABASE_KEY)
        return cls._instance

supabase = SupabaseClient.get_instance()

# Define a Pydantic model for the incoming request body
class QuestionRequest(BaseModel):
    """
    Model for incoming question request data.
    
    Attributes:
        question (Union[str, None]): User's question. Default is None.
        llm (str): Language model to use for processing. Default is "meta-llama/llama-3.1-70b-instruct".
        personality (str): Personality type for the bot. Default is "delhi".
        personality_prompt (str): Custom personality prompt for the bot.
        last_three_responses (str): Contextual history from the last three responses.
    """
    question: Union[str, None] = None  # Question from the user
    llm: str = "meta-llama/llama-3.1-70b-instruct"  # Default language model
    personality: str = "delhi"  # Personality type
    personality_prompt: str = ""  # Personality prompt 
    last_three_responses: str = ""  # Context from last three responses


# Define the endpoint for chat functionality
@app.post("/cv/chat")
async def cv_chat(request: QuestionRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to handle chatbot queries.

    Args:
        request (QuestionRequest): Input data containing user's question and related configuration.
        background_tasks (BackgroundTasks): Tasks to be performed asynchronously.

    Returns:
        dict: A response from the chatbot or an error message if the process fails.

    Example:
        Input:
        {
            "question": "What is the history of Delhi?",
            "llm": "meta-llama/llama-3.1-70b-instruct",
            "personality": "city",
            "personality_prompt": "",
            "last_three_responses": "Explained about Delhi city."
        }

        Output:
        {
             "response": "The Red Fort was constructed by Mughal Emperor Shah Jahan in 1648 as the palace of his fortified capital Shahjahanabad.",
            "cit": 4.34,
            "drt": 34.43,
            "rgt": 345.22
        }
    """
    try:
        # Validate if the question is provided and not empty
        if not request.question or request.question.strip() == "":
            return {"error": str("Please provide a question")}  # Return error if invalid



        # Generate bot response using the provided information and language model
        bot_response = get_response_by_bot(
            request.question, cit, drt, request.llm, request.personality_prompt, request.last_three_responses
        )

        # Ensure bot response is in the correct format (dictionary with a "response" key)
        if isinstance(bot_response, dict) and "response" in bot_response:
            response_data = bot_response["response"]
        else:
            return {"error": "Bot response format is invalid"}  # Return error if invalid

        # Log the input question, relative info, and bot response
        logging.info(f"Question: {request.question}")
        logging.info(f"Response: {response_data}")

        

        return bot_response
    
    # Handle any exceptions that occur during execution
    except Exception as e:
        logging.info(f"Error: {e}")  # Log the error for debugging
        print("Error:", e)
        return {"error": str("Error occurred while generating the quiz and summary")}  # Return error message
