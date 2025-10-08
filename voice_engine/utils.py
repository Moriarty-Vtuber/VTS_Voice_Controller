import os
import requests
import tarfile
from pathlib import Path
from tqdm import tqdm
from loguru import logger
import sys # Import sys
import shutil

def get_github_asset_url(owner, repo, release_tag, filename_without_ext):
    """
    Fetch the URL of a GitHub release asset by its filename (without extension).

    Args:
        owner (str): The owner of the repository.
        repo (str): The name of the repository.
        release_tag (str): The tag of the release.
        filename_without_ext (str): The filename to search for (without extension).

    Returns:
        str: The download URL of the matched asset, or None if no match is found.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{release_tag}"
    headers = {}  # Add authentication headers if needed

    try:
        # Make a GET request to fetch release data
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        release_data = response.json()
        assets = release_data.get("assets", [])

        # Look for a matching file
        for asset in assets:
            if asset["name"].startswith(filename_without_ext):
                logger.info(f"Match found: {asset['name']}")
                return asset["browser_download_url"]

        # If no match found, log the error
        logger.error(
            f"No match found for filename: {filename_without_ext} in release {release_tag}."
        )
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while fetching release data: {e}")
        return None


def ensure_model_downloaded_and_extracted(url: str, output_dir: str) -> Path:
    """
    Ensures the model archive is downloaded and extracted, handling checks for existing files.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    file_name = url.split("/")[-1]
    compressed_file_path = Path(output_dir) / file_name

    model_name = file_name.replace(".tar.bz2", "")
    extracted_dir_path = Path(output_dir) / model_name # This is the top-level extracted dir

    # Determine the potential final model directory (could be nested)
    potential_final_model_dir = extracted_dir_path
    if extracted_dir_path.exists():
        extracted_items = os.listdir(extracted_dir_path)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(extracted_dir_path, extracted_items[0])):
            potential_final_model_dir = Path(extracted_dir_path) / extracted_items[0]

    expected_files = ["encoder-epoch-99-avg-1.int8.onnx", "decoder-epoch-99-avg-1.int8.onnx", "joiner-epoch-99-avg-1.int8.onnx", "tokens.txt"]
    all_files_exist = all(os.path.isfile(os.path.join(potential_final_model_dir, f)) for f in expected_files)

    if potential_final_model_dir.exists() and all_files_exist:
        logger.info(f"✅ Model already extracted and complete at {potential_final_model_dir}. Skipping download/extraction.")
        return potential_final_model_dir
    elif extracted_dir_path.exists(): # If top-level exists but files are missing/incomplete, clean up
        logger.warning(f"Extracted directory {extracted_dir_path} exists but is missing some expected files or is incomplete. Re-extracting.")
        shutil.rmtree(extracted_dir_path) # Clean up incomplete directory

    # 1. Ensure the compressed file is downloaded
    if not compressed_file_path.exists():
        disable_tqdm = getattr(sys, 'frozen', False)
        logger.info(f"🏃‍♂️Downloading {url} to {compressed_file_path}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        logger.debug(f"Total file size: {total_size / 1024 / 1024:.2f} MB")

        with (
            open(compressed_file_path, "wb") as f,
            tqdm(
                desc=file_name,
                total=total_size,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
                disable=disable_tqdm
            ) as pbar,
        ):
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                pbar.update(size)
        logger.info(f"Downloaded {file_name} successfully.")
    else:
        logger.info(f"Compressed file {file_name} already exists. Skipping download.")

    # 3. Extract the archive
    logger.info(f"Extracting {file_name} to {extracted_dir_path}...")
    extracted_dir_path.mkdir(parents=True, exist_ok=True)
    with tarfile.open(compressed_file_path, "r:bz2") as tar:
        tar.extractall(path=extracted_dir_path)
    logger.info("Extraction completed.")

    # 4. Determine final model directory after extraction (handling nested)
    final_model_dir_after_extraction = extracted_dir_path
    extracted_items = os.listdir(extracted_dir_path)
    if len(extracted_items) == 1 and os.path.isdir(os.path.join(extracted_dir_path, extracted_items[0])):
        final_model_dir_after_extraction = Path(extracted_dir_path) / extracted_items[0]
        logger.info(f"Found nested directory after extraction: {final_model_dir_after_extraction}.")

    # 5. Delete the compressed file
    os.remove(compressed_file_path)
    logger.debug(f"Deleted the compressed file: {file_name}")

    return final_model_dir_after_extraction


# Remove the old download_and_extract and check_and_extract_local_file functions
# as their logic is now consolidated into ensure_model_downloaded_and_extracted.
# The following lines are placeholders for removal.
# def download_and_extract(...): ...
# def check_and_extract_local_file(...): ...

if __name__ == "__main__":
    url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2"
    output_dir = "./models"

    # Try local extraction first.
    local_result = ensure_model_downloaded_and_extracted(url, output_dir)
    logger.info(f"Model ensured at: {local_result}")
