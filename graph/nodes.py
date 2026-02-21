import logging
import os
from pathlib import Path
from uuid import uuid4

# Absolute path to the project root (parent of the graph/ package)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from graph.state import AICompanionState
from graph.utils.chains import get_conversation_chain, get_router_chain
from graph.utils.helpers import (
    get_chat_model,
    get_image_to_text_module,
    get_text_to_image_module,
    get_text_to_speech_module,
)
from modules.memory.memory_manager import get_memory_manager
from settings import settings

logger = logging.getLogger(__name__)


async def router_node(state: AICompanionState):
    logger.info("[router_node] Determining workflow...")
    chain = get_router_chain()
    response = await chain.ainvoke({"messages": state["messages"][-settings.ROUTER_MESSAGES_TO_ANALYZE:]})
    logger.info(f"[router_node] Workflow selected: '{response.response_type}'")
    return {"workflow": response.response_type}


async def conversation_node(state: AICompanionState, config: RunnableConfig):
    logger.info("[conversation_node] Generating text response...")
    memory_context = state.get("memory_context", "")
    if memory_context:
        logger.info(f"[conversation_node] Memory context injected:\n{memory_context}")
    chain = get_conversation_chain(state.get("summary", ""))
    response = await chain.ainvoke(
        {"messages": state["messages"], "memory_context": memory_context},
        config,
    )
    logger.info(f"[conversation_node] Response: {response[:120]}..." if len(response) > 120 else f"[conversation_node] Response: {response}")
    return {"messages": AIMessage(content=response)}


async def image_node(state: AICompanionState, config: RunnableConfig):
    logger.info("[image_node] Starting image generation flow...")
    memory_context = state.get("memory_context", "")
    chain = get_conversation_chain(state.get("summary", ""))
    text_to_image_module = get_text_to_image_module()

    logger.info("[image_node] Creating image scenario from conversation...")
    scenario = await text_to_image_module.create_scenario(state["messages"][-5:])
    logger.info(f"[image_node] Image prompt: {scenario.image_prompt}")

    img_dir = _PROJECT_ROOT / settings.GENERATED_IMAGE_DIR
    img_dir.mkdir(parents=True, exist_ok=True)
    img_path = str(img_dir / f"image_{str(uuid4())}.png")
    logger.info(f"[image_node] Calling RapidAPI Flux to generate image -> {img_path}")
    img_path = await text_to_image_module.generate_image(scenario.image_prompt, img_path)
    logger.info(f"[image_node] Image saved: {img_path}")

    scenario_message = HumanMessage(content=f"<image generated from prompt: {scenario.image_prompt}>")
    updated_messages = state["messages"] + [scenario_message]

    response = await chain.ainvoke(
        {"messages": updated_messages, "memory_context": memory_context},
        config,
    )
    logger.info(f"[image_node] Text response: {response[:120]}..." if len(response) > 120 else f"[image_node] Text response: {response}")
    return {"messages": AIMessage(content=response), "image_path": img_path}


async def audio_node(state: AICompanionState, config: RunnableConfig):
    logger.info("[audio_node] Generating audio response...")
    memory_context = state.get("memory_context", "")
    chain = get_conversation_chain(state.get("summary", ""))
    text_to_speech_module = get_text_to_speech_module()

    response = await chain.ainvoke(
        {"messages": state["messages"], "memory_context": memory_context},
        config,
    )
    logger.info(f"[audio_node] Text to synthesize: {response[:120]}..." if len(response) > 120 else f"[audio_node] Text to synthesize: {response}")
    logger.info("[audio_node] Calling TTS...")
    output_audio = await text_to_speech_module.synthesize(response)
    logger.info(f"[audio_node] Audio generated: {len(output_audio)} bytes")
    audio_dir = _PROJECT_ROOT / settings.GENERATED_AUDIO_DIR
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = str(audio_dir / f"audio_{str(uuid4())}.mp3")
    with open(audio_path, "wb") as f:
        f.write(output_audio)
    logger.info(f"[audio_node] Audio saved: {audio_path}")
    return {"messages": AIMessage(content=response), "audio_buffer": output_audio, "audio_path": audio_path}


async def summarize_conversation_node(state: AICompanionState):
    logger.info(f"[summarize_node] Message count ({len(state['messages'])}) exceeded threshold. Summarizing...")
    model = get_chat_model()
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is the summary of the conversation so far: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = (
            "Create a summary of the conversation above. "
            "The summary must be a short description capturing all relevant information shared:"
        )

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = await model.ainvoke(messages)
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-settings.TOTAL_MESSAGES_AFTER_SUMMARY]]
    logger.info(f"[summarize_node] Summary updated. Removed {len(delete_messages)} old messages.")
    return {"summary": response.content, "messages": delete_messages}


async def memory_extraction_node(state: AICompanionState):
    logger.info("[memory_extraction_node] Analyzing last message for memory...")
    if not state["messages"]:
        logger.info("[memory_extraction_node] No messages found, skipping.")
        return {}
    memory_manager = get_memory_manager()
    await memory_manager.extract_and_store_memories(state["messages"][-1])
    return {}


def memory_injection_node(state: AICompanionState):
    logger.info("[memory_injection_node] Retrieving relevant memories from Qdrant...")
    memory_manager = get_memory_manager()
    recent_context = " ".join([m.content for m in state["messages"][-3:]])
    memories = memory_manager.get_relevant_memories(recent_context)
    memory_context = memory_manager.format_memories_for_prompt(memories)
    if memory_context:
        logger.info(f"[memory_injection_node] Injecting {len(memories)} memories into context.")
    else:
        logger.info("[memory_injection_node] No relevant memories found.")
    return {"memory_context": memory_context}

