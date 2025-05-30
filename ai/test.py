import pyaudio
import speech_recognition as sr
import threading
import queue
import time
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import requests 
# Initialize recognizer and model
recognizer = sr.Recognizer()
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')  # Multilingual model for Vietnamese
audio_queue = queue.Queue()
awaiting_command = False  

command_list = ['tắt đèn', 'bật đèn', 'mở nhạc', 'tắt nhạc']
command_embeddings = model.encode(command_list)

def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                   channels=CHANNELS,
                   rate=RATE,
                   input=True,
                   frames_per_buffer=CHUNK)
    
    print("Recording... Say 'xin chào' followed by your command.")
    
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_queue.put(data)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        audio_queue.put(None)

def process_audio():
    global awaiting_command
    audio_data = []
    last_audio_time = time.time()
    
    while True:
        data = audio_queue.get()
        if data is None:
            break
        audio_data.append(data)
        
        current_time = time.time()
        elapsed_time = current_time - last_audio_time
        process_interval = 3 if awaiting_command else 2 
        
        if elapsed_time > process_interval:
            try:
                audio = sr.AudioData(b''.join(audio_data), 16000, 2)
                
                def recognize():
                    global awaiting_command
                    try:
                        text = recognizer.recognize_google(audio, language='vi-VN').lower()
                        print(f"Heard: {text}")
                        
                        if text.strip() == "xin chào" and not awaiting_command:
                            awaiting_command = True
                            print("Waiting for command...")
                        elif awaiting_command:
                            spoken_embedding = model.encode([text])[0]
                            similarities = cosine_similarity([spoken_embedding], command_embeddings)[0]
                            max_similarity = np.max(similarities)
                            if max_similarity > 0.7:  
                                command_idx = np.argmax(similarities)
                                command = command_list[command_idx]
                                print(f"Command: {command} (Similarity: {max_similarity:.2f})")
                                print(f"Executing command: {command}")
                                url = ""
                                if command == 'tắt đèn':
                                    url = "https://api.kdth-smarthome.space/led/off"
                                elif command == 'bật đèn':
                                    url = "https://api.kdth-smarthome.space/led/on"
                                elif command == 'mở nhạc':
                                    pass
                                elif command == 'tắt nhạc':
                                    pass
                                response = requests.get(url)
                                if response.status_code == 200:
                                    print("Dữ liệu từ API:", response)
                                else:
                                    print("Lỗi khi gọi API, mã lỗi:", response.status_code)
                            else:
                                print("Command not recognized (low similarity).")
                            awaiting_command = False  
                            
                    except sr.UnknownValueError:
                        pass  
                    except sr.RequestError as e:
                        print(f"Error: {e}")
                
                threading.Thread(target=recognize, daemon=True).start()
                
                audio_data = []
                last_audio_time = current_time
                
            except Exception as e:
                print(f"Processing error: {e}")
                
        audio_queue.task_done()

def main():
    print("Starting real-time speech to text with 'xin chào' trigger and embedding-based command recognition...")
    
    record_thread = threading.Thread(target=record_audio)
    process_thread = threading.Thread(target=process_audio)
    
    record_thread.start()
    process_thread.start()
    
    try:
        record_thread.join()
        process_thread.join()
    except KeyboardInterrupt:
        print("\nStopped recording.")
    finally:
        print("Program stopped.")

if __name__ == "__main__":
    main()