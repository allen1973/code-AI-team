import hashlib
import numpy as np
from pathlib import Path

# 注意：我們在函數內部或局部引入 AI 庫，避免沒裝環境的人報錯
def get_md5(file_path: Path):
    """計算檔案 MD5 (分塊讀取)"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def predict_image_category(model, img_path: Path, confidence_threshold: float):
    """AI 內容辨識 (MobileNetV2)"""
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
    from tensorflow.keras.preprocessing import image
    
    try:
        img = image.load_img(img_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = model.predict(x, verbose=0)
        _, label, prob = decode_predictions(preds, top=1)[0][0]
        
        if prob >= confidence_threshold:
            return label.lower().replace(" ", "_")
        return "uncertain_content"
    except Exception:
        return "error_processing"
