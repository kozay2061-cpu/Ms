from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os, tempfile
import numpy as np
import librosa

app = Flask(__name__, static_folder='.', static_url_path='')
MAX_UPLOAD_MB = 40
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.webm'}
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MAJOR = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
MINOR = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])

def pearson(a, b):
    if np.std(a) < 1e-9 or np.std(b) < 1e-9: return 0.0
    return float(np.corrcoef(a, b)[0, 1])

def estimate_key(chroma):
    profile = np.mean(chroma, axis=1)
    best = (-2, 'Unknown')
    for root in range(12):
        maj = np.roll(MAJOR, root)
        minor = np.roll(MINOR, root)
        for score, label in [(pearson(profile, maj), f'{NOTES[root]} major'), (pearson(profile, minor), f'{NOTES[root]} minor')]:
            if score > best[0]: best = (score, label)
    return best[1], round(max(0, best[0]) * 100)

def chord_labels(chroma, times):
    # Basic triad-template matching; estimates, not guaranteed transcription.
    templates = []
    for root in range(12):
        for quality, intervals in [('major', [0,4,7]), ('minor', [0,3,7]), ('dim', [0,3,6])]:
            vec = np.zeros(12)
            for interval in intervals: vec[(root + interval) % 12] = 1
            templates.append((f"{NOTES[root]}" + ('' if quality == 'major' else 'm' if quality == 'minor' else 'dim'), vec))
    # one chord estimate per roughly half-second frame, then collapse consecutive repeats
    norm = chroma / (np.max(chroma, axis=0, keepdims=True) + 1e-9)
    detected = []
    for i in range(norm.shape[1]):
        vec = norm[:, i]
        scores = [(float(np.dot(vec, t) / (np.sum(t) + 1e-9)), name) for name, t in templates]
        score, name = max(scores)
        t = float(times[i]) if i < len(times) else i * 0.5
        if detected and detected[-1]['chord'] == name:
            detected[-1]['end_sec'] = round(t, 2)
        else:
            detected.append({'chord': name, 'start_sec': round(t, 2), 'end_sec': round(t, 2), 'confidence_estimate': round(score * 100)})
    return [x for x in detected if x['end_sec'] - x['start_sec'] >= 0.35][:100]

def guess_style(bpm):
    if bpm < 65: return 'Slow Ballad / Ambient (rough guess)'
    if bpm < 90: return 'Ballad / Slow Pop (rough guess)'
    if bpm < 115: return 'Pop / Mid-tempo (rough guess)'
    if bpm < 140: return 'Pop Rock / Dance (rough guess)'
    return 'Fast Rock / Dance (rough guess)'

@app.get('/')
def home():
    return send_from_directory('.', 'online.html')

@app.get('/health')
def health():
    return jsonify({'ok': True, 'service': 'AI Music Studio analysis API', 'mode': 'signal-processing estimates'})

@app.post('/api/analyze')
def analyze():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file was uploaded.'}), 400
    f = request.files['audio']
    ext = os.path.splitext(secure_filename(f.filename or 'audio.wav'))[1].lower()
    if ext not in ALLOWED:
        return jsonify({'error': 'Unsupported file type. Try MP3, WAV, M4A, OGG, FLAC, AAC or WEBM.'}), 400
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            temp_path = tmp.name
            f.save(temp_path)
        y, sr = librosa.load(temp_path, sr=22050, mono=True, duration=180)
        if len(y) < sr * 2:
            return jsonify({'error': 'Audio is too short to analyze; use at least 2 seconds.'}), 400
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
        bpm = float(np.atleast_1d(tempo)[0])
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=1024)
        key, key_confidence = estimate_key(chroma)
        chord_times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=1024)
        chords = chord_labels(chroma, chord_times)
        duration = float(len(y) / sr)
        return jsonify({
            'filename': secure_filename(f.filename or 'audio'),
            'duration_sec': round(duration, 2),
            'bpm_estimate': round(bpm, 1),
            'beat_times_sec': [round(x, 3) for x in beat_times[:500]],
            'key_estimate': key,
            'key_confidence_estimate_pct': key_confidence,
            'time_signature': {'value': 'Not reliably detected', 'note': 'Set meter manually; bar count below defaults to 4/4.'},
            'bars_estimate_4_4': round((duration * bpm / 60) / 4, 1),
            'style_guess': guess_style(bpm),
            'chords_estimate': chords,
            'limitations': 'Signal-processing estimates, not guaranteed transcription. Style is a tempo heuristic. Chords/key may be wrong for dense mixes. No separate neural genre-classification model is connected.'
        })
    except Exception as e:
        app.logger.exception('Analysis failed')
        return jsonify({'error': 'Audio analysis failed. Check the file format and try a shorter file.', 'detail': str(e)[:250]}), 500
    finally:
        if temp_path and os.path.exists(temp_path): os.remove(temp_path)

if __name__ == '__main__':
    # For local testing only. For public hosting, use a production WSGI server and HTTPS.
    app.run(host='127.0.0.1', port=5000, debug=False)
