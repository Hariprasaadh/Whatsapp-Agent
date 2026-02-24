from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

from prompts import AUDIO_PROMPT, CONVERSATION_PROMPT, IMAGE_CAPTION_PROMPT, ROUTER_PROMPT
from graph.utils.helpers import AsteriskRemovalParser, get_chat_model


class RouterResponse(BaseModel):
    response_type: str = Field(
        description="The response type to give to the user. It must be one of: 'conversation', 'image' or 'audio'"
    )


def get_router_chain():
    model = get_chat_model(temperature=0.3).with_structured_output(RouterResponse)
    prompt = ChatPromptTemplate.from_messages(
        [("system", ROUTER_PROMPT), MessagesPlaceholder(variable_name="messages")]
    )
    return prompt | model


def get_image_caption_chain(summary: str = ""):
    system_message = IMAGE_CAPTION_PROMPT
    if summary:
        system_message += f"\n\nSummary of conversation so far: {summary}"
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | get_chat_model() | AsteriskRemovalParser()


def get_audio_chain(summary: str = ""):
    system_message = AUDIO_PROMPT
    if summary:
        system_message += f"\n\nSummary of conversation so far: {summary}"
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | get_chat_model() | AsteriskRemovalParser()


def get_conversation_chain(summary: str = ""):
    system_message = CONVERSATION_PROMPT
    if summary:
        system_message += f"\n\nSummary of conversation so far: {summary}"
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | get_chat_model() | AsteriskRemovalParser()
