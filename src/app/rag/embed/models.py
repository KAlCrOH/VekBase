from __future__ import annotations

from dataclasses import dataclass
import torch


@dataclass
class ModelConfig:
    name: str
    device: str
    dtype: str


def resolve_model(name: str) -> ModelConfig:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = "float16" if device == "cuda" else "float32"
    return ModelConfig(name=name, device=device, dtype=dtype)
