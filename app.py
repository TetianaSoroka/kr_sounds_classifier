import gradio as gr
import joblib
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

MAX_DURATION = 12

model = joblib.load("project/model.pkl")


def extract_features(audio_path):
    y, sr = librosa.load(audio_path, sr=None, duration=MAX_DURATION)

    mels = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=20)
    mels_db = librosa.power_to_db(mels, ref=np.max)

    zcr = librosa.feature.zero_crossing_rate(y)

    return np.hstack([
        np.mean(mels_db, axis=1),
        np.std(mels_db, axis=1),
        np.mean(zcr, axis=1),
        np.std(zcr, axis=1)
    ])


def make_spectrogram(audio_path):
    y, sr = librosa.load(audio_path, sr=None, duration=MAX_DURATION)

    mels = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    mels_db = librosa.power_to_db(mels, ref=np.max)

    fig, ax = plt.subplots(figsize=(8, 4))
    img = librosa.display.specshow(
        mels_db,
        sr=sr,
        x_axis="time",
        y_axis="mel",
        ax=ax
    )

    ax.set_title("Спектрограма Мела")
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    plt.tight_layout()

    return fig


def predict_audio(audio_file):
    audio_path = audio_file.name

    features = extract_features(audio_path)

    prediction = model.predict(
        features.reshape(1, -1)
    )[0]

    spectrogram = make_spectrogram(audio_path)

    return str(prediction), spectrogram


demo = gr.Interface(
    fn=predict_audio,
    inputs=gr.File(
        label="Завантажте аудіофайл",
        file_types=[".wav", ".mp3"]
    ),
    outputs=[
        gr.Textbox(label="Клас звуку"),
        gr.Plot(label="Спектрограма")
    ],
    title="Класифікатор звуків",
    description="Класифікація аудіозаписів та побудова Mel-спектрограми.",
    submit_btn="Класифікувати",
    clear_btn="Очистити",
    flagging_mode="never"
)

demo.launch()