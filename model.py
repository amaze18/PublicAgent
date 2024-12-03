import time 
import json
import asyncio
from utils import call_groq_api

def get_response_by_bot(question,cit, drt,model,personality_prompt,last_three_responses):
    """
        Generates a chatbot response based on user input, contextual information, and personality.

        Args:
            question (str): The user's question.
            cit (str): Citation or source for the information, if available.
            drt (float): Data retrieval time in milliseconds.
            model (str): Language model used to generate the response.
            personality_prompt (str): Personality-specific instructions for the bot.
            last_three_responses (str): Context of the last three responses for continuity.

        Returns:
            dict: A dictionary containing the bot's response, citation, data retrieval time (drt),
                and response generation time (rgt).

        Example:
            Input:
                question = "What is the capital of India?"
                relative_info = "Delhi is the capital of India."
                cit = 34.32
                drt = 556.45
                model = "meta-llama/llama-3.1-70b-instruct"
                personality_prompt = "Energetic and concise, like a true Delhiite!"
                last_three_responses = "Answered questions about Indian geography."

            Output:
                {
                    "response": "The capital of India is New Delhi, known for its rich history and vibrant culture.",
                    "cit" : 34.32
                    "drt" : 556.45
                    "rgt": 123.45
                }
    """
    # Start Response Generation Time measurement
    start_rgt = time.time()

    # Prepare the bot prompt
    bot_prompt ="""
    ## Instruction
        {personality_prompt}
        Here is relative information about you: {relative_info}
        NOTE: If there’s any relevant info about you, I’ll weave it into the chat naturally, so it feels personalized. But if it’s not available or doesn’t quite match the conversation, I’ll focus on the here and now, keeping the energy high and the talk flowing. No need to bring it up unless it’s useful, we’re just vibing!
        Response should not be long, keep it small and to the point.
        - Dont add translations
    ## Last 3 Responses you have given
        {last_three_responses}
    ## User Question
    Answer the user question:{question}
    """.replace("{question}", question).replace("{personality_prompt}",personality_prompt).replace("{last_three_responses}",last_three_responses)

    # Call the API to get the response
    bot_prompt_response = call_groq_api(bot_prompt)

    # Calculate Response Generation Time (RGT)
    rgt = round((time.time() - start_rgt) * 1000, 2)  # in milliseconds

    # Prepare the final response
    response_json = {
        "response": bot_prompt_response,
        "cit": cit,
        "drt": drt,
        "rgt": rgt
    }
    return response_json

_all = [
    "get_response_by_bot"
]
