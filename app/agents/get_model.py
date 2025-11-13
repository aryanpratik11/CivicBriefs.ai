# get_model.py
import os
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import RepositoryNotFoundError
from huggingface_hub import HfApi

# get_model.py
from dotenv import load_dotenv
load_dotenv()
import sys

REPO_ID = "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF"
FNAME = "llama-3.2-1b-instruct-q4_k_m.gguf"
LOCAL_DIR = "models"

def get_token():
    # common env vars huggingface-hub looks for
    return os.environ.get("HUGGINGFACE_TOKEN2") or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")

def main():
    token = get_token()
    if not token:
        print("No HF token found in environment. Either run `huggingface-cli login` or set HUGGINGFACE_HUB_TOKEN env var.")
        print("Example (PowerShell): $env:HUGGINGFACE_HUB_TOKEN = 'hf_xxx...'")
        sys.exit(1)

    try:
        print(f"Attempting to download {FNAME} from {REPO_ID} → {LOCAL_DIR} ...")
        path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FNAME,
            local_dir=LOCAL_DIR,
            token=token,          # explicitly pass token
            force_filename=FNAME
        )
        print("Downloaded model to:", path)
    except RepositoryNotFoundError as e:
        print("Repository not found / you might not have access to this repo.")
        print("Make sure you have requested/accepted access to the model on Hugging Face and that your token has read scope.")
        raise
    except Exception as e:
        # Many possible exceptions: auth/gated repo etc
        print("Error while trying to download. Common causes:")
        print("- The model repo is gated and you haven't accepted the license or requested access.")
        print("- Your token is invalid or missing 'read' scope.")
        print("Fix steps:")
        print("  1) Open https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct and accept the terms/request access.")
        print("  2) Generate a token in HF settings (read scope) and run `huggingface-cli login` or set HUGGINGFACE_HUB_TOKEN.")
        print("Then re-run this script.")
        raise

if __name__ == "__main__":
    main()


# downlaod the quantized Llama-3.2-1B-Instruct (1B parameters) from huggingface 