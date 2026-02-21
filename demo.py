import asyncio
import logging
import time

from langchain_core.messages import HumanMessage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

print("[startup] Loading modules... (this may take 10-30s on first run)")
from graph.graph import graph
print("[startup] All modules loaded. Ready.\n")


async def run(messages: list) -> list:
    print(f"\n[pipeline] Starting graph with {len(messages)} message(s)...")
    t0 = time.time()
    result = await graph.ainvoke({"messages": messages})
    elapsed = time.time() - t0

    last = result["messages"][-1]
    print(f"\n[Agent]: {last.content}")
    print(f"[pipeline] Completed in {elapsed:.2f}s")

    if result.get("audio_buffer"):
        with open("demo_audio.mp3", "wb") as f:
            f.write(result["audio_buffer"])
        print("[Audio saved]: demo_audio.mp3")

    if result.get("image_path"):
        print(f"[Image saved]: {result['image_path']}")

    return result["messages"]


if __name__ == "__main__":
    print("=== WhatsApp Agent Demo ===")
    print("Type 'quit' to exit\n")
    print("Tips:")
    print("  - Normal message     → conversation response")
    print("  - 'send me an image' → image generation")
    print("  - 'say that out loud' → voice note (saved as demo_audio.mp3)\n")

    async def loop():
        history = []
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("quit", "exit"):
                break
            if not user_input:
                continue
            history.append(HumanMessage(content=user_input))
            history = await run(history)

    asyncio.run(loop())

