"""Stable boundary for the future multimodal subsystem."""

class VisionAdapter:
    async def analyze(self, image: bytes, instruction: str = "") -> dict:
        return {"status": "not_configured", "instruction": instruction, "bytes": len(image)}
