import os
from flask import Flask, render_template, request, send_file
from PIL import Image
import cv2
import numpy as np
from rembg import remove
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Pastikan folder upload ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def enhance_image(image_path):
    """Fungsi untuk meningkatkan kualitas foto dengan tetap mempertahankan detail"""
    try:
        # Baca gambar
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError("Gagal membaca gambar")
        
        # 1. Perbaikan kontras dengan CLAHE
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l_eq = clahe.apply(l)
        
        lab_enhanced = cv2.merge((l_eq, a, b))
        enhanced_img = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        # 2. Reduksi noise dengan bilateral filter
        enhanced_img = cv2.bilateralFilter(enhanced_img, 9, 75, 75)
        
        return enhanced_img
    
    except Exception as e:
        print(f"Error dalam enhance_image: {e}")
        # Kembalikan gambar asli jika gagal
        return cv2.imread(image_path)

def compress_image(image_path, quality=80):
    """Fungsi untuk mengompres foto"""
    img = Image.open(image_path)
    compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], 'compressed_' + os.path.basename(image_path))
    img.save(compressed_path, optimize=True, quality=quality)
    return compressed_path

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/remove_background', methods=['POST'])
def remove_background():
    if 'file' not in request.files:
        return 'Tidak ada file yang diunggah', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'Tidak ada file yang dipilih', 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Hapus background
    input_image = Image.open(filepath)
    output_image = remove(input_image)
    
    # Simpan sebagai PNG untuk mendukung transparansi
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'nobg_' + os.path.splitext(filename)[0] + '.png')
    output_image.save(output_path, format='PNG')
    
    return send_file(output_path, mimetype='image/png')

@app.route('/enhance_image', methods=['POST'])
def enhance_photo():
    if 'file' not in request.files:
        return 'Tidak ada file yang diunggah', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'Tidak ada file yang dipilih', 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        # Proses enhance
        enhanced_img = enhance_image(filepath)
        
        # Simpan gambar hasil
        enhanced_path = os.path.join(app.config['UPLOAD_FOLDER'], 'enhanced_' + filename)
        cv2.imwrite(enhanced_path, enhanced_img)
        
        return send_file(enhanced_path, mimetype='image/png')
    except Exception as e:
        print(f"Error dalam proses enhance: {e}")
        return f'Gagal meningkatkan kualitas gambar: {str(e)}', 500

@app.route('/compress_image', methods=['POST'])
def compress_photo():
    if 'file' not in request.files:
        return 'Tidak ada file yang diunggah', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'Tidak ada file yang dipilih', 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Kompres foto
    compressed_path = compress_image(filepath)
    
    return send_file(compressed_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)