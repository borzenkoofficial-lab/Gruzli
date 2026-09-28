"""Optional QLoRA entrypoint."""
def main():
    try:
        import transformers
        import peft
    except ImportError as exc:
        raise SystemExit("Install training extras: pip install -e '.[training]'") from exc
    print("QLoRA dependencies are available.")
    print("Next: bind a selected base model and verified SFT dataset.")

if __name__ == "__main__":
    main()
