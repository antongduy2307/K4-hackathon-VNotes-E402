from providers.openai_provider import OpenAIProvider


def make_provider(name: str):
    if name == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unknown provider: {name} (only 'openai' is wired up for this agent)")
