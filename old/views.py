import os
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import time
import pandas as pd


# helper functions and classes
from .utils import OutputDataframe, allowed_file, secure_filename
from .processing import FileProcessingHandler,FuzzyLookupHelper

class ColumnNamesApiView(APIView):
    def post(self, request):
        if 'file' not in request.FILES:
            return Response({'error': 'No file part'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        user_id = request.user.id  # Assuming the user is authenticated and you have access to `request.user`
        
        # Check if a file is selected
        if file.name == '':
            return Response({'error': 'No selected file'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the file is allowed
        if allowed_file(file.name):
            # Create a user-specific directory if it does not exist
            user_directory = os.path.join(settings.MEDIA_ROOT, f"user_{user_id}")
            if not os.path.exists(user_directory):
                os.makedirs(user_directory)

            # Create a unique sub-folder based on UUID
            unique_id = uuid.uuid4()
            sub_directory = os.path.join(user_directory, f"{file.name}_{unique_id}")
            if not os.path.exists(sub_directory):
                os.makedirs(sub_directory)

            # Secure the filename and create the full file path
            filename = secure_filename(user_id, file.name)
            file_path = os.path.join(sub_directory, filename)

            # Save the file in the user-specific directory
            default_storage.save(file_path, ContentFile(file.read()))

            try:
                # Use the OutputDataframe class to handle file conversion
                output_df = OutputDataframe(file_path)
                df = output_df.convert_to_dataframe()
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # Extract column names and map each to itself
            column_dict = {column_name: column_name for column_name in df.columns}

            return Response({'filename': filename, 'column_names': column_dict}, status=status.HTTP_200_OK)

        return Response({'error': 'File not allowed'}, status=status.HTTP_400_BAD_REQUEST)


class FuzzyLookupMultiApiView(APIView):
    """
    /api/fuzzylookup
    """

    def post(self, request):
        postData = request.data
        file_name_1 = postData.get('file_name_1')
        file_name_2 = postData.get('file_name_2')
        file_1_column = postData.get('file_1_column')
        file_2_column = postData.get('file_2_column')
        threshold = float(postData.get('threshold') / 100)
        # algo_method = postData.get('algo_method')
        # join_method = postData.get('join_method')
        # ignore_case = bool(postData.get('ignore_case'))
        delimiter = postData.get('delimiter', ',')
        if len(delimiter) > 1:
            delimiter = "\t"
        output_type = postData.get('output_type')

        # Define file paths (adjust according to your file saving logic)
        file_name_1_processed_path = os.path.join(settings.MEDIA_ROOT, file_name_1)
        print(file_name_1_processed_path)
        file_name_2_processed_path = os.path.join(settings.MEDIA_ROOT, file_name_2)

        try:
            # Use the helper class for preprocessing the files
            file_name_1_processed_df = FuzzyLookupHelper.fuzzy_lookup_preprocess(file_name_1_processed_path, file_1_column)
            file_name_2_processed_df = FuzzyLookupHelper.fuzzy_lookup_preprocess(file_name_2_processed_path, file_2_column)

            # Use the helper class to perform fuzzy lookup
            matches = FuzzyLookupHelper.fuzzylookup_main(file_name_1_processed_df, file_name_2_processed_df, file_1_column, file_2_column, threshold)

            # Post-process the matches using the helper class
            data_df = FuzzyLookupHelper.fuzzylookup_postprocess(matches, file_name_1_processed_df, file_name_2_processed_df, file_1_column, file_2_column, join_method)

            # Generate output file name and save the processed file
            output_file_name = time.strftime("%Y%m%d-%H%M%S")
            output_path = os.path.join(settings.MEDIA_ROOT, 'downloads')

            if output_type == 'xlsx':
                output_file = f'{output_file_name}.xlsx'
                data_df.to_excel(os.path.join(output_path, output_file), index=False)
            elif output_type == 'csv':
                output_file = f'{output_file_name}.csv'
                data_df.to_csv(os.path.join(output_path, output_file), sep=delimiter, index=False)

            # Return the processed file for download
            with open(os.path.join(output_path, output_file), 'rb') as f:
                response = HttpResponse(f.read(), content_type=f'text/{output_type}')
                response['Content-Disposition'] = f'attachment; filename="{output_file}"'
                return response

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 
class LookupSingleFileApiView(APIView):
    def post(self, request):
        # Retrieve the original filename, column names, and threshold from request data
        original_filename = request.data.get('filename')
        column_1 = request.data.get('column_1')
        column_2 = request.data.get('column_2')
        threshold = float(request.data.get('threshold'))
        user_id = request.user.id

        # Extract the base filename from the original filename (strip the UUID part for directory search)
        base_filename = original_filename.split('_')[1]

        # Locate the sub-directory where the file is saved
        user_directory = os.path.join(settings.MEDIA_ROOT, f"user_{user_id}")
        
        # Locate the sub-directory that contains the original filename (with UUID)
        sub_directory = None
        for folder in os.listdir(user_directory):
            if base_filename in folder:
                sub_directory = os.path.join(user_directory, folder)
                break

        if not sub_directory or not os.path.exists(sub_directory):
            return Response({'error': 'Sub-directory for the original file not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Load the original file from the sub-directory
        original_file_path = os.path.join(sub_directory, original_filename)

        if not os.path.exists(original_file_path):
            return Response({'error': 'Original file not found.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Use the OutputDataframe class to load the file again
            output_df = OutputDataframe(original_file_path)
            df = output_df.convert_to_dataframe()

            # Process the DataFrame
            # Pass threshold when initializing the FileProcessingHandler class
            file_processor = FileProcessingHandler(df, threshold)
            processed_df = file_processor.pre_process_dataframe(column_1, column_2)

            # Save the processed file to the sub-directory
            processed_file_path = os.path.join(sub_directory, f"processed_{original_filename}")

            # Save the processed file
            processed_df.to_csv(processed_file_path, index=False)

            # Return the processed file for download
            with open(processed_file_path, 'rb') as processed_file:
                response = HttpResponse(processed_file.read(), content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(processed_file_path)}"'
                return response

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

