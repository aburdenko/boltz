from flask import Flask, request, jsonify
import numpy as np
from boltz.model.model import Boltz1  # Import the Boltz1 model
from boltz.data.module.inference import BoltzInferenceDataModule
from boltz.data.types import Manifest
from boltz.data.write.writer import BoltzWriter
from boltz.data.parse.a3m import parse_a3m
from boltz.data.parse.csv import parse_csv
from boltz.data.types import MSA
from pathlib import Path
from dataclasses import asdict
from boltz.main import BoltzDiffusionParams
import torch
from pytorch_lightning import Trainer
import pickle
from boltz.main import CCD_URL
import urllib.request
import click
from google.cloud import storage
import tempfile
import os


app = Flask(__name__)

# Set the environment variable for Google Cloud project ID if needed
os.environ['GOOGLE_CLOUD_PROJECT'] = 'kallogjeri-project-345114'

# Initialize your Boltz model (simplified example - adapt as needed)
# **Important**:  Refer to boltz repo for proper initialization parameters!
model = None
data_module=None
predict_args = {}
diffusion_params = None
pred_writer=None
cache=Path("/boltz/cache").expanduser()

def download(cache: Path) -> None:
    """Download all the required data.

    Parameters
    ----------
    cache : Path
        The cache directory.

    """
    # Download CCD
    ccd = cache / "ccd.pkl"
    if not ccd.exists():
        click.echo(
            f"Downloading the CCD dictionary to {ccd}. You may "
            "change the cache directory with the --cache flag."
        )
        urllib.request.urlretrieve(CCD_URL, str(ccd))  # noqa: S310

    # Download model
    model = cache / "boltz1_conf.ckpt"
    if not model.exists():
        click.echo(
            f"Downloading the model weights to {model}. You may "
            "change the cache directory with the --cache flag."
        )
        urllib.request.urlretrieve(
            "https://huggingface.co/boltz-community/boltz-1/resolve/main/boltz1_conf.ckpt", str(model)
        )
    
    
try:
    cache.mkdir(parents=True, exist_ok=True)

    download(cache)
    # Load CCD
    with (cache / "ccd.pkl").open("rb") as file:
      ccd = pickle.load(file)  # noqa: S301

    # Load processed data
    processed_dir = Path("/boltz/processed")
    
    manifest = Manifest(records=[])
    if (processed_dir / "manifest.json").exists():
      manifest = Manifest.load(processed_dir / "manifest.json")

    processed = {
        "manifest": manifest,
        "targets_dir": processed_dir / "structures",
        "msa_dir": processed_dir / "msa",
    }
    
    # Create data module
    data_module = BoltzInferenceDataModule(
        manifest=processed["manifest"],
        target_dir=processed["targets_dir"],
        msa_dir=processed["msa"],
        num_workers=0,
    )
    

    # Load model
    checkpoint = cache / "boltz1_conf.ckpt"

    predict_args = {
        "recycling_steps": 3,
        "sampling_steps": 200,
        "diffusion_samples": 1,
        "write_confidence_summary": True,
        "write_full_pae": False,
        "write_full_pde": False,
    }
    diffusion_params = BoltzDiffusionParams()
    diffusion_params.step_scale = 1.638
    model: Boltz1 = Boltz1.load_from_checkpoint(
        checkpoint,
        strict=True,
        predict_args=predict_args,
        map_location="cpu",
        diffusion_process_args=asdict(diffusion_params),
        ema=False,
    )
    model.eval()

    pred_writer = BoltzWriter(
        data_dir=processed["targets_dir"],
        output_dir="/boltz/predictions",
        output_format="mmcif",
    )
    
    print("Boltz model initialized successfully.")
except Exception as e:
    print(f"Error initializing Boltz model: {e}")
    model = None  # Handle initialization failure

def download_from_gcs(bucket_name, blob_name):
    """Downloads a file from Google Cloud Storage to a temporary file."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        blob.download_to_filename(tmp_file.name)
        print(f"File {blob_name} downloaded to {tmp_file.name}.")
        return tmp_file.name


def process_fasta(path: str):
    """Processes a FASTA file and returns a list of target IDs."""
    # In this case, we assume that the file is a valid fasta file, and that
    # each fasta id is a target_id. This is not a general case, but it is valid
    # for most cases.
    try:
      with open(path, 'r') as file:
        sequences = file.read()
        lines = sequences.splitlines()
        target_ids = [line.replace(">", "") for line in lines if line.startswith(">")]
        return target_ids
    except Exception as e:
      raise Exception(f"Error processing fasta file: {e}")



@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Boltz model not initialized'}), 500

    try:
        request_data = request.get_json()
        if not request_data or 'instances' not in request_data:
            return jsonify({'error': 'Invalid request format. Expecting JSON with "instances" key.'}), 400

        bucket_name = request_data.get("bucket")
        blob_name = request_data.get("blob")

        if not bucket_name or not blob_name:
            return jsonify({'error': 'Bucket name and blob name must be provided'}), 400

        temp_fasta_file = download_from_gcs(bucket_name, blob_name)

        instances = process_fasta(temp_fasta_file)

        # Remove the temporary file
        os.remove(temp_fasta_file)

        # dummy data for inference
        # assuming we get target_ids, lets create dummy input data for each target_id.
        data_module.target_ids = instances
        trainer = Trainer(
            default_root_dir="/boltz",
            strategy="auto",
            callbacks=[pred_writer],
            accelerator="cpu",
            devices=1,
            precision=32,
        )

        # Compute predictions
        trainer.predict(
            model,
            datamodule=data_module,
            return_predictions=False,
        )

        # return dummy data
        predictions_list = instances

        return jsonify({'predictions': predictions_list})

    except Exception as e:
        return jsonify({'error': str(e)}), 400



@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
