import numpy as np
import tensorflow as tf
from django.conf import settings
import cv2
import os

model = None

def get_model():
    global model
    if model is None:
        model = tf.keras.models.load_model(settings.MODEL_PATH)
    return model

def predict(image_path):
    m = get_model()
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (456, 456))
    img = img.astype(np.float32)  # no preprocessing, just resize

    augmented = [
        img,
        np.fliplr(img),
        np.flipud(img),
        np.rot90(img, 1),
        np.rot90(img, 3),
    ]

    all_preds = []
    for aug_img in augmented:
        img_array = np.expand_dims(aug_img, axis=0)
        preds = m.predict(img_array, verbose=0)
        all_preds.append(preds[0])

    avg_preds = np.mean(all_preds, axis=0)
    grade = int(np.argmax(avg_preds))
    confidence = float(np.max(avg_preds)) * 100
    grades = ['No DR', 'Mild', 'Moderate', 'Severe', 'Proliferative DR']
    return grade, confidence, grades[grade]

def generate_gradcam(image_path, save_path):
    m = get_model()

    last_conv_layer = None
    for layer in reversed(m.layers):
        if hasattr(layer, 'filters'):
            last_conv_layer = layer.name
            break

    if last_conv_layer is None:
        return

    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img, (456, 456))
    img_array = tf.cast(np.expand_dims(img_resized, axis=0), tf.float32)

    grad_model = tf.keras.models.Model(
        inputs=m.inputs,
        outputs=[m.get_layer(last_conv_layer).output, m.output]
    )

    with tf.GradientTape() as tape:
        tape.watch(img_array)
        last_conv_output, preds = grad_model(img_array)
        if isinstance(preds, list):
            preds = preds[-1]
        pred_index = int(np.argmax(preds.numpy().flatten()))
        class_channel = preds[0][pred_index % preds.shape[-1]]

    grads = tape.gradient(class_channel, last_conv_output)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    heatmap = last_conv_output[0] @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
    heatmap = heatmap.numpy()

    heatmap_resized = cv2.resize(heatmap, (456, 456))
    heatmap_colored = cv2.applyColorMap(np.uint8(255 * heatmap_resized), cv2.COLORMAP_JET)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    superimposed = cv2.addWeighted(img_resized, 0.6, heatmap_colored, 0.4, 0)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cv2.imwrite(save_path, cv2.cvtColor(superimposed, cv2.COLOR_RGB2BGR))