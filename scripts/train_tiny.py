from nexum_core.model.tiny import train_smoke

if __name__ == "__main__":
    loss = train_smoke()
    print(f"final loss: {loss:.4f}")
