import chainlit as cl

async def process_chainlit_request(message: str, user):
    # Initialize Chainlit
    cl.user_session.set("user", user)

    # Process the message using Chainlit
    response = await cl.Message(content=message).send()

    return response.content
