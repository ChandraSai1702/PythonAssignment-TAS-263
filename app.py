from flask import Flask, render_template, request, redirect, url_for, flash
import boto3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

AWS_ACCESS_KEY = 'AKIA6JKEYGAG7DCEHZLV'
AWS_SECRET_ACCESS_KEY = 'V2ZxgiuCf2H9sjhkproouPJVTpTpTQltH3zYLM5P'
REGION = 'eu-north-1'
S3_BUCKET = 'chandrasai'

# Initialize S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION
)


# Route to list contents of the S3 bucket
@app.route('/')
def index():
    contents = list_s3_content()
    folders = get_folders(contents)
    return render_template('index.html', contents=contents, folders=folders)


# List all objects and folders in the bucket
def list_s3_content():
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET)
        contents = response.get('Contents', [])
        return contents
    except Exception as e:
        flash(f"Error: {str(e)}")
        return []


# Extract folder names from S3 contents
def get_folders(contents):
    folders = set()
    for item in contents:
        key = item['Key']
        if key.endswith('/'):
            folders.add(key)
    return sorted(folders)


# Route to create a folder
@app.route('/create-folder', methods=['POST'])
def create_folder():
    folder_name = request.form['folder_name']
    if folder_name:
        folder_name = folder_name.rstrip('/') + '/'
        try:
            s3.put_object(Bucket=S3_BUCKET, Key=folder_name)
            flash('Folder created successfully!')
        except Exception as e:
            flash(f"Error: {str(e)}")
    return redirect(url_for('index'))


# Route to delete a folder or file
@app.route('/delete', methods=['POST'])
def delete_object():
    key = request.form['key']
    try:
        s3.delete_object(Bucket=S3_BUCKET, Key=key)
        flash('Deleted successfully!')
    except Exception as e:
        flash(f"Error: {str(e)}")
    return redirect(url_for('index'))


# Route to upload a file with selected folder
@app.route('/upload', methods=['POST'])
def upload_file():
    folder = request.form.get('folder')
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if folder:
        file_key = f"{folder}{file.filename}"
    else:
        file_key = file.filename

    try:
        s3.upload_fileobj(file, S3_BUCKET, file_key)
        flash('File uploaded successfully!')
    except Exception as e:
        flash(f"Error: {str(e)}")

    return redirect(url_for('index'))


# Route to move or copy a file
@app.route('/move-copy', methods=['POST'])
def move_copy_file():
    src_key = request.form['src_key']
    dest_key = request.form['dest_key']
    action = request.form['action']

    try:
        if action == 'copy':
            s3.copy_object(Bucket=S3_BUCKET, CopySource={'Bucket': S3_BUCKET, 'Key': src_key}, Key=dest_key)
            flash('File copied successfully!')
        elif action == 'move':
            s3.copy_object(Bucket=S3_BUCKET, CopySource={'Bucket': S3_BUCKET, 'Key': src_key}, Key=dest_key)
            s3.delete_object(Bucket=S3_BUCKET, Key=src_key)
            flash('File moved successfully!')
    except Exception as e:
        flash(f"Error: {str(e)}")

    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True,port='5055')