import cv2
import numpy as np
import mss
import pyaudio
import wave
import threading
import time

def record_screen(stop_event, video_filename, fps=20.0, monitor_index=1):
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        width = monitor["width"]
        height = monitor["height"]
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
        
        print("화면 녹화를 시작합니다...")
        last_time = time.time()
        while not stop_event.is_set():
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            elapsed = time.time() - last_time
            sleep_time = max(0, 1/fps - elapsed)
            time.sleep(sleep_time)
            last_time = time.time()
        out.release()
        print("화면 녹화가 종료되었습니다.")

def record_system_audio_stereo_mix(stop_event, audio_filename, channels=2, rate=44100, frames_per_buffer=1024):
    p = pyaudio.PyAudio()
    
    # 장치 목록에서 "스테레오 믹스"가 포함된 장치를 찾습니다.
    stereo_mix_device_index = None
    for i in range(p.get_device_count()):
        device = p.get_device_info_by_index(i)
        if "스테레오 믹스" in device['name']:
            stereo_mix_device_index = i
            break
    if stereo_mix_device_index is None:
        print("스테레오 믹스 장치를 찾을 수 없습니다.")
        p.terminate()
        return

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=rate,
            input=True,
            frames_per_buffer=frames_per_buffer,
            input_device_index=stereo_mix_device_index
        )
    except Exception as e:
        print("오디오 스트림을 열 수 없습니다:", e)
        p.terminate()
        return

    frames = []
    print("시스템(스테레오 믹스) 오디오 녹음을 시작합니다...")
    while not stop_event.is_set():
        try:
            data = stream.read(frames_per_buffer, exception_on_overflow=False)
            frames.append(data)
        except Exception as e:
            print("오디오 데이터 읽기 중 오류 발생:", e)
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(audio_filename, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(rate)
    wf.writeframes(b"".join(frames))
    wf.close()
    print("시스템 오디오 녹음이 종료되었습니다.")

def main():
    video_filename = "output_video.avi"
    audio_filename = "output_audio.wav"
    stop_event = threading.Event()

    video_thread = threading.Thread(target=record_screen, args=(stop_event, video_filename))
    audio_thread = threading.Thread(target=record_system_audio_stereo_mix, args=(stop_event, audio_filename))
    
    video_thread.start()
    audio_thread.start()
    
    print("녹화를 진행 중입니다. 중지하려면 Ctrl+C를 누르세요...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n녹화를 중지합니다...")
        stop_event.set()
    
    video_thread.join()
    audio_thread.join()
    
    print("녹화가 완료되었습니다.")
    print(f"영상 파일: {video_filename}")
    print(f"오디오 파일: {audio_filename}")
    print("\n두 파일을 하나로 합치려면 ffmpeg 등을 이용할 수 있습니다.")
    print(f"  ffmpeg -y -i {video_filename} -i {audio_filename} -c:v copy -c:a aac output_merged.mp4")

if __name__ == "__main__":
    main()
