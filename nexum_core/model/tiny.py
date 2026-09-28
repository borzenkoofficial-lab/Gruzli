"""Tiny trainable language-model smoke test."""
from pathlib import Path
import torch
from torch import nn

class TinyLM(nn.Module):
    def __init__(self, vocab_size=128, hidden=64):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, hidden)
        self.rnn = nn.GRU(hidden, hidden, batch_first=True)
        self.head = nn.Linear(hidden, vocab_size)

    def forward(self, x):
        h, _ = self.rnn(self.embed(x))
        return self.head(h)

def train_smoke(steps=100, checkpoint="checkpoints/nexum-tiny.pt"):
    torch.manual_seed(7)
    model = TinyLM()
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
    data = torch.randint(0, 128, (16, 32))
    target = data.roll(-1, dims=1)
    for _ in range(steps):
        logits = model(data)
        loss = nn.functional.cross_entropy(logits.reshape(-1, 128), target.reshape(-1))
        opt.zero_grad()
        loss.backward()
        opt.step()
    Path(checkpoint).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint)
    return float(loss.detach())
