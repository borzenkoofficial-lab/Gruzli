from nexum_core.training.prepare_sft import prepare

if __name__ == "__main__":
    print(prepare("datasets/raw/trajectories.jsonl", "datasets/processed/sft.jsonl"))
