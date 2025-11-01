import os
import requests
import tarfile
from tqdm import tqdm
from loguru import logger


def ensure_model_downloaded_and_extracted(model_url: str, model_base_dir: str) -> str:
    """Downloads and extracts the ASR model if not already present."""
    model_name = model_url.split("/")[-1].replace(".tar.bz2", "")
    model_dir = os.path.join(model_base_dir, model_name)
    archive_path = os.path.join(model_base_dir, os.path.basename(model_url))

    # Check if the model directory already exists and seems complete
    if os.path.exists(model_dir) and os.path.exists(os.path.join(model_dir, "tokens.txt")):
        logger.info(
            f"✅ Model already extracted and complete at {model_dir}. Skipping download/extraction.")
        return model_dir

    os.makedirs(model_base_dir, exist_ok=True)

    # Download the model
    logger.info(f"Downloading ASR model from {model_url}...")
    try:
        with requests.get(model_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(archive_path, 'wb') as f, tqdm(
                desc=model_name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    bar.update(size)
        logger.info("Download complete.")
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise

    # Extract the model
    logger.info(f"Extracting model to {model_dir}...")
    try:
        with tarfile.open(archive_path, "r:bz2") as tar:
            tar.extractall(path=model_base_dir)
        logger.info("Extraction complete.")
    except Exception as e:
        logger.error(f"Failed to extract model: {e}")
        raise
    finally:
        # Clean up the downloaded archive
        if os.path.exists(archive_path):
            os.remove(archive_path)

    return model_dir
