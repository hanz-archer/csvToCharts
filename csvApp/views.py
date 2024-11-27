import os
import uuid
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import render

def index(request):
    return render(request, 'csvApp/index.html')

def csv(request):
    chart_url = None
    error = None
    csv_files = []
    chart_files = []

    # Path to the media directory for CSV and chart files
    media_csv_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
    media_chart_path = os.path.join(settings.MEDIA_ROOT, 'generated_charts')

    # Get the list of existing files for the sidebar
    if os.path.exists(media_csv_path):
        csv_files = [f for f in os.listdir(media_csv_path) if f.endswith('.csv')]

    if os.path.exists(media_chart_path):
        chart_files = [f for f in os.listdir(media_chart_path) if f.endswith('.png')]

    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            # Get the uploaded CSV file and chart type
            csv_file = request.FILES['csv_file']
            chart_type = request.POST.get('chart_type', 'bar')

            # Save the file to the MEDIA_ROOT
            file_path = default_storage.save(f'uploads/{csv_file.name}', ContentFile(csv_file.read()))
            file_url = default_storage.url(file_path)

            try:
                # Read the CSV file into a Pandas DataFrame
                df = pd.read_csv(default_storage.open(file_path))

                # Generate the chart
                plt.figure(figsize=(10, 6))

                if chart_type == 'bar':
                    df.plot(kind='bar', ax=plt.gca())
                elif chart_type == 'line':
                    df.plot(kind='line', ax=plt.gca())
                elif chart_type == 'pie':
                    if len(df.columns) >= 2:
                        df.iloc[:, 1].plot(kind='pie', labels=df.iloc[:, 0], autopct='%1.1f%%', ax=plt.gca())
                elif chart_type == 'scatter':
                    if len(df.columns) >= 2:
                        plt.scatter(df.iloc[:, 0], df.iloc[:, 1])
                        plt.xlabel(df.columns[0])
                        plt.ylabel(df.columns[1])

                # Save the chart to a BytesIO object
                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                plt.close()
                buffer.seek(0)

                # Generate a unique filename for the chart
                chart_filename = f'generated_chart_{uuid.uuid4().hex}.png'
                chart_path = os.path.join(media_chart_path, chart_filename)

                # Ensure the directory exists
                os.makedirs(os.path.dirname(chart_path), exist_ok=True)

                # Save the chart image to the media directory
                with open(chart_path, 'wb') as f:
                    f.write(buffer.getvalue())

                # Set the chart URL for rendering in the template
                chart_url = f'/media/generated_charts/{chart_filename}'

                # Update the list of CSV and chart files
                csv_files = [f for f in os.listdir(media_csv_path) if f.endswith('.csv')]
                chart_files = [f for f in os.listdir(media_chart_path) if f.endswith('.png')]

            except pd.errors.EmptyDataError:
                error = "The CSV file is empty or invalid."
            except pd.errors.ParserError:
                error = "There was an error parsing the CSV file. Please ensure it's in the correct format."
            except Exception as e:
                error = f"An unexpected error occurred: {e}"

    return render(request, 'csvApp/csv.html', {
        'chart_url': chart_url,
        'error': error,
        'csv_files': csv_files,
        'chart_files': chart_files
    })
