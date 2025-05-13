import requests
import uuid
import time

# === CONFIGURATION ===
USERNAME = "abc123123123@gmail.com"
PASSWORD = "aaaaaa"
VOICE_TOKEN = "weight_883h5cw4q48cpsmjvjypxs0dc"  # Peter Griffin
TEXT = "Hey Lois, I'm on FakeYou!"
OUTPUT_FILENAME = "peter_griffin.wav"

# === LOGIN ===
session = requests.Session()
credentials = {
    "username_or_email": USERNAME,
    "password": PASSWORD
}

login_response = session.post("https://api.fakeyou.com/v1/login", json=credentials)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit()
print("✅ Logged in successfully.")

# === SUBMIT TTS JOB ===
job_payload = {
    "tts_model_token": VOICE_TOKEN,
    "uuid_idempotency_token": str(uuid.uuid4()),
    "inference_text": TEXT
}

job_response = session.post("https://api.fakeyou.com/tts/inference", json=job_payload)

if job_response.status_code != 200:
    print(f"❌ Failed to start TTS job: {job_response.text}")
    exit()

inference_job_token = job_response.json().get("inference_job_token")
print(f"📨 Submitted TTS job: {inference_job_token}")

# === POLL FOR COMPLETION ===
poll_url = f"https://api.fakeyou.com/tts/job/{inference_job_token}"
audio_path = None

print("⏳ Waiting for job to complete...")
for attempt in range(60):  # Poll for up to 60 seconds
    time.sleep(1)
    response = session.get(poll_url)

    if response.status_code != 200:
        print(f"❌ Poll error: HTTP {response.status_code}")
        print(response.text)
        break

    try:
        data = response.json()
    except Exception:
        print("❌ Failed to parse JSON from response:")
        print(response.text)
        break

    job_status = data.get('state', {}).get('status')
    audio_path = data.get('state', {}).get('maybe_public_bucket_wav_audio_path')

    print(f"🔁 Status: {job_status}")

    if job_status == 'complete_success' and audio_path:
        break
    elif job_status in ['dead', 'attempt_failed']:
        print(f"❌ Job failed with status: {job_status}")
        exit()

if not audio_path:
    print("❌ Job completed but no audio path found.")
    exit()

# === DOWNLOAD THE AUDIO FILE (Try Both CDNs) ===
audio_url_primary = f"https://cdn.fakeyou.com{audio_path}"
audio_url_fallback = f"https://cdn-2.fakeyou.com{audio_path}"

print(f"📥 Trying to download from: {audio_url_primary}")
audio_response = session.get(audio_url_primary)

if audio_response.status_code != 200:
    print(f"⚠️ Failed on cdn.fakeyou.com (HTTP {audio_response.status_code}), trying fallback...")
    audio_response = session.get(audio_url_fallback)
    audio_url = audio_url_fallback
else:
    audio_url = audio_url_primary

# Save the file if download worked
if audio_response.status_code == 200:
    with open(OUTPUT_FILENAME, "wb") as f:
        f.write(audio_response.content)
    print(f"✅ Audio saved as '{OUTPUT_FILENAME}' from {audio_url}")
else:
    print(f"❌ Failed to download audio from both CDNs (HTTP {audio_response.status_code})")
