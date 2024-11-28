import os
import uuid
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import render
from django.contrib import messages

def index(request):
    return render(request, 'csvApp/index.html')

def csv(request):
    chart_url = None

    # Paths to the media directories
    media_csv_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
    media_chart_path = os.path.join(settings.MEDIA_ROOT, 'generated_charts')

    # Ensure the directories exist
    os.makedirs(media_csv_path, exist_ok=True)
    os.makedirs(media_chart_path, exist_ok=True)

    # Get the list of existing files for the sidebar
    csv_files = [{'name': f, 'url': f'/media/uploads/{f}'} for f in os.listdir(media_csv_path) if f.endswith('.csv')]
    chart_files = [{'name': f, 'url': f'/media/generated_charts/{f}'} for f in os.listdir(media_chart_path) if f.endswith('.png')]

    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            chart_type = request.POST.get('chart_type', 'bar')

            # Save the CSV file
            file_path = default_storage.save(f'uploads/{csv_file.name}', ContentFile(csv_file.read()))

            try:
                # Generate chart from CSV
                df = pd.read_csv(default_storage.open(file_path))
                plt.figure(figsize=(10, 6))

                if chart_type == 'bar':
                    df.plot(kind='bar', ax=plt.gca())
                elif chart_type == 'line':
                    df.plot(kind='line', ax=plt.gca())
                elif chart_type == 'pie' and len(df.columns) >= 2:
                    df.iloc[:, 1].plot(kind='pie', labels=df.iloc[:, 0], autopct='%1.1f%%', ax=plt.gca())
                elif chart_type == 'scatter' and len(df.columns) >= 2:
                    plt.scatter(df.iloc[:, 0], df.iloc[:, 1])
                    plt.xlabel(df.columns[0])
                    plt.ylabel(df.columns[1])

                buffer = BytesIO()
                plt.savefig(buffer, format='png')
                plt.close()
                buffer.seek(0)

                chart_filename = f'generated_chart_{uuid.uuid4().hex}.png'
                chart_path = os.path.join(media_chart_path, chart_filename)

                with open(chart_path, 'wb') as f:
                    f.write(buffer.getvalue())

                chart_url = f'/media/generated_charts/{chart_filename}'

                # Refresh file lists
                csv_files = [{'name': f, 'url': f'/media/uploads/{f}'} for f in os.listdir(media_csv_path) if f.endswith('.csv')]
                chart_files = [{'name': f, 'url': f'/media/generated_charts/{f}'} for f in os.listdir(media_chart_path) if f.endswith('.png')]

            except Exception as e:
                messages.error(request, f"An error occurred: {e}")

    return render(request, 'csvApp/csv.html', {
        'chart_url': chart_url,
        'csv_files': csv_files,
        'chart_files': chart_files,
    })

