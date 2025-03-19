from flask import Flask, request, jsonify
import asyncio
import os

app = Flask(__name__)

# Mock functions (replace with your actual implementations)
async def download_from_gcs(bucket_name, blob_name):
    temp_fasta_file = "temp_fasta_file.txt"
    with open(temp_fasta_file, "w") as f:
        f.write(">sequence1\nATGCGTAGCTAGCTAGCTAGC\n")
    return temp_fasta_file

async def process_fasta(temp_fasta_file):
    return ["target1", "target2"]

async def run_prediction(instances):
    return [f"prediction_{i}" for i in instances]

@app.route('/', methods=['GET', 'POST'])  # Add GET method
@app.route('/predict', methods=['GET', 'POST'])  # Add GET method
async def predict():
    # if request.method == 'GET':
    #     return "Please send a POST request with the instances to predict."  # Simple message for GET requests

    try:
        request_data = request.get_json()
        # if not request_data or 'instances' not in request_data:
        #     return jsonify({'error': 'Invalid request format. Expecting JSON with "instances" key.'}), 400

        bucket_name = request_data.get("bucket")
        blob_name = request_data.get("blob")

        if not bucket_name or not blob_name:
            bucket_name = "boltz"
            blob_name = "ligand.fasta"

        temp_fasta_file = await download_from_gcs(bucket_name, blob_name)

        instances = await process_fasta(temp_fasta_file)

        os.remove(temp_fasta_file)

        predictions_list = await run_prediction(instances)

        return jsonify({'predictions': predictions_list})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, debug=True)
