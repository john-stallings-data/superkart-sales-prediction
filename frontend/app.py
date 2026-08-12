
# Import libraries required by the Streamlit application
import os

import pandas as pd
import requests
import streamlit as st


# Read the backend address from the container environment
# The default address uses the backend container name
BACKEND_URL = os.getenv(
    'BACKEND_URL',
    'http://backend:7860'
).rstrip('/')

REQUEST_TIMEOUT = 120


# Configure the Streamlit page
st.set_page_config(
    page_title='SuperKart Sales Prediction',
    page_icon='🛒',
    layout='centered'
)

st.title('SuperKart Sales Prediction')
st.write(
    'Enter product and store information to estimate '
    'the total sales revenue.'
)


# Create separate areas for single and batch inference
single_tab, batch_tab = st.tabs([
    'Single Prediction',
    'Batch Prediction'
])


with single_tab:
    st.subheader('Product and Store Information')

    product_weight = st.number_input(
        'Product Weight',
        min_value=0.0,
        value=12.66,
        step=0.01
    )

    product_sugar_content = st.selectbox(
        'Product Sugar Content',
        [
            'Low Sugar',
            'Regular',
            'No Sugar'
        ]
    )

    product_allocated_area = st.number_input(
        'Product Allocated Area',
        min_value=0.0,
        max_value=1.0,
        value=0.056,
        step=0.001,
        format='%.3f'
    )

    product_type = st.selectbox(
        'Product Type',
        [
            'Baking Goods',
            'Breads',
            'Breakfast',
            'Canned',
            'Dairy',
            'Frozen Foods',
            'Fruits and Vegetables',
            'Hard Drinks',
            'Health and Hygiene',
            'Household',
            'Meat',
            'Others',
            'Seafood',
            'Snack Foods',
            'Soft Drinks',
            'Starchy Foods'
        ]
    )

    product_mrp = st.number_input(
        'Product MRP',
        min_value=0.0,
        value=146.74,
        step=0.01
    )

    store_size = st.selectbox(
        'Store Size',
        [
            'Small',
            'Medium',
            'High'
        ]
    )

    store_location_city_type = st.selectbox(
        'Store Location City Type',
        [
            'Tier 1',
            'Tier 2',
            'Tier 3'
        ]
    )

    store_type = st.selectbox(
        'Store Type',
        [
            'Departmental Store',
            'Food Mart',
            'Supermarket Type1',
            'Supermarket Type2'
        ]
    )

    # Build the JSON request using the original model features
    product_data = {
        'Product_Weight': product_weight,
        'Product_Sugar_Content': product_sugar_content,
        'Product_Allocated_Area': product_allocated_area,
        'Product_Type': product_type,
        'Product_MRP': product_mrp,
        'Store_Size': store_size,
        'Store_Location_City_Type': store_location_city_type,
        'Store_Type': store_type
    }

    if st.button(
        'Predict Sales',
        type='primary',
        use_container_width=True
    ):
        try:
            with st.spinner('Generating the sales prediction...'):
                response = requests.post(
                    f'{BACKEND_URL}/v1/predict',
                    json=product_data,
                    timeout=REQUEST_TIMEOUT
                )

            if response.ok:
                prediction_result = response.json()
                predicted_sales = prediction_result['Sales']

                st.success(
                    'Predicted Product Store Sales Total: '
                    f'{predicted_sales:,.2f}'
                )

            else:
                try:
                    error_message = response.json().get(
                        'error',
                        'The prediction request failed.'
                    )
                except ValueError:
                    error_message = (
                        'The prediction request failed.'
                    )

                st.error(
                    f'API error {response.status_code}: '
                    f'{error_message}'
                )

        except requests.RequestException as error:
            st.error(
                'The frontend could not connect to the '
                f'prediction API: {error}'
            )


with batch_tab:
    st.subheader('Upload Batch Data')

    st.write(
        'Upload a CSV file containing the eight predictor '
        'columns required by the model.'
    )

    uploaded_file = st.file_uploader(
        'Choose a CSV file',
        type=['csv']
    )

    if uploaded_file is not None:
        try:
            # Read the file for preview and later result display
            batch_preview = pd.read_csv(uploaded_file)

            st.write(
                f'Rows detected: {len(batch_preview):,}'
            )

            st.dataframe(
                batch_preview.head(10),
                use_container_width=True
            )

            if st.button(
                'Predict Batch Sales',
                type='primary',
                use_container_width=True
            ):
                # Reset the uploaded file before sending it
                uploaded_file.seek(0)

                files = {
                    'file': (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        'text/csv'
                    )
                }

                with st.spinner(
                    'Generating batch predictions...'
                ):
                    response = requests.post(
                        f'{BACKEND_URL}/v1/predictbatch',
                        files=files,
                        timeout=REQUEST_TIMEOUT
                    )

                if response.ok:
                    batch_result = response.json()
                    predictions = batch_result['Predictions']

                    if len(predictions) != len(batch_preview):
                        st.error(
                            'The number of returned predictions '
                            'does not match the uploaded rows.'
                        )

                    else:
                        completed_results = batch_preview.copy()

                        completed_results[
                            'Predicted_Sales'
                        ] = predictions

                        st.success(
                            f'{len(predictions):,} predictions '
                            'completed successfully.'
                        )

                        st.dataframe(
                            completed_results,
                            use_container_width=True
                        )

                        st.download_button(
                            label='Download Predictions',
                            data=completed_results.to_csv(
                                index=False
                            ).encode('utf-8'),
                            file_name=(
                                'SuperKart_Batch_Predictions.csv'
                            ),
                            mime='text/csv',
                            use_container_width=True
                        )

                else:
                    try:
                        error_message = response.json().get(
                            'error',
                            'The batch request failed.'
                        )
                    except ValueError:
                        error_message = (
                            'The batch request failed.'
                        )

                    st.error(
                        f'API error {response.status_code}: '
                        f'{error_message}'
                    )

        except pd.errors.ParserError:
            st.error(
                'The uploaded file could not be read as CSV.'
            )

        except requests.RequestException as error:
            st.error(
                'The frontend could not connect to the '
                f'prediction API: {error}'
            )
