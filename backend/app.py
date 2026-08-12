
# Import libraries required by the prediction API
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request


# Create the Flask application
superkart_api = Flask('SuperKart')

# Limit uploaded batch files to 10 megabytes
superkart_api.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024


# Define the features expected by the serialized model pipeline
EXPECTED_FEATURES = [
    'Product_Weight',
    'Product_Sugar_Content',
    'Product_Allocated_Area',
    'Product_Type',
    'Product_MRP',
    'Store_Size',
    'Store_Location_City_Type',
    'Store_Type'
]

NUMERICAL_FEATURES = [
    'Product_Weight',
    'Product_Allocated_Area',
    'Product_MRP'
]


# Locate the model relative to this application file
MODEL_PATH = (
    Path(__file__).resolve().parent
    / 'superkart_model.joblib'
)

# Load the complete preprocessing and model pipeline
model = joblib.load(MODEL_PATH)


def prepare_input(input_data):
    """
    Validate and prepare input data for model prediction.
    """

    # Identify any required columns that were not provided
    missing_features = [
        feature
        for feature in EXPECTED_FEATURES
        if feature not in input_data.columns
    ]

    if missing_features:
        raise ValueError(
            'Missing required features: '
            + ', '.join(missing_features)
        )

    # Retain the expected columns in their required order
    prepared_data = input_data[EXPECTED_FEATURES].copy()

    # Confirm that numerical inputs contain valid numbers
    for feature in NUMERICAL_FEATURES:
        prepared_data[feature] = pd.to_numeric(
            prepared_data[feature],
            errors='raise'
        )

    return prepared_data


@superkart_api.get('/')
def home():
    """
    Confirm that the SuperKart API is available.
    """

    return jsonify({
        'message': 'Welcome to the SuperKart Sales Prediction API',
        'single_prediction_endpoint': '/v1/predict',
        'batch_prediction_endpoint': '/v1/predictbatch'
    })


@superkart_api.get('/health')
def health():
    """
    Provide a health check for the deployed service.
    """

    return jsonify({
        'status': 'healthy',
        'model_loaded': True
    })


@superkart_api.post('/v1/predict')
def predict_sales():
    """
    Predict sales for one product and store observation.
    """

    if not request.is_json:
        return jsonify({
            'error': 'The request body must contain JSON data.'
        }), 400

    input_json = request.get_json(silent=True)

    if not isinstance(input_json, dict):
        return jsonify({
            'error': 'A valid JSON object is required.'
        }), 400

    try:
        # Convert the JSON observation into a one row DataFrame
        input_data = pd.DataFrame([input_json])

        prepared_data = prepare_input(input_data)

        # Generate and return one sales prediction
        prediction = float(
            model.predict(prepared_data)[0]
        )

        return jsonify({
            'Sales': round(prediction, 2)
        })

    except (ValueError, TypeError) as error:
        return jsonify({
            'error': str(error)
        }), 400

    except Exception:
        superkart_api.logger.exception(
            'An unexpected prediction error occurred.'
        )

        return jsonify({
            'error': 'The prediction could not be completed.'
        }), 500


@superkart_api.post('/v1/predictbatch')
def predict_sales_batch():
    """
    Predict sales for multiple observations supplied in a CSV file.
    """

    if 'file' not in request.files:
        return jsonify({
            'error': 'A CSV file is required.'
        }), 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return jsonify({
            'error': 'The uploaded file does not have a filename.'
        }), 400

    try:
        # Read and validate the uploaded CSV data
        input_data = pd.read_csv(uploaded_file)

        if input_data.empty:
            return jsonify({
                'error': 'The uploaded CSV file is empty.'
            }), 400

        prepared_data = prepare_input(input_data)

        # Generate sales predictions for every row
        predictions = model.predict(
            prepared_data
        ).tolist()

        rounded_predictions = [
            round(float(prediction), 2)
            for prediction in predictions
        ]

        return jsonify({
            'Count': len(rounded_predictions),
            'Predictions': rounded_predictions
        })

    except (ValueError, TypeError, pd.errors.ParserError) as error:
        return jsonify({
            'error': str(error)
        }), 400

    except Exception:
        superkart_api.logger.exception(
            'An unexpected batch prediction error occurred.'
        )

        return jsonify({
            'error': 'The batch prediction could not be completed.'
        }), 500


if __name__ == '__main__':
    superkart_api.run(
        host='0.0.0.0',
        port=7860,
        debug=False
    )
