import cv2
import numpy as np
import mss
import pyaudio
import wave
import threading
import time

def record_screen(stop_event, video_filename, fps=20.0, monitor_index=1):
    """
    화면을 캡처하여 영상 파일로 저장하는 함수입니다.
    
    Args:
        stop_event (threading.Event): 녹화 중지를 알리는 이벤트.
        video_filename (str): 저장할 영상 파일 이름 (예: "output_video.avi").
        fps (float): 초당 프레임 수.
        monitor_index (int): 캡처할 모니터 인덱스 (mss에서는 1부터 시작).
    """
    with mss.mss() as sct:
        # 기본 모니터를 선택 (여러 모니터가 있을 경우 index 선택)
        monitor = sct.monitors[monitor_index]
        width = monitor["width"]
        height = monitor["height"]

        # OpenCV VideoWriter 설정 (XVID 코덱 사용)
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
        
        print("화면 녹화를 시작합니다...")
        last_time = time.time()
        while not stop_event.is_set():
            # 모니터 전체 캡처
            img = np.array(sct.grab(monitor))
            # mss는 기본적으로 BGRA 형식이므로 BGR로 변환
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            
            # FPS를 맞추기 위한 딜레이 계산
            elapsed = time.time() - last_time
            sleep_time = max(0, 1/fps - elapsed)
            time.sleep(sleep_time)
            last_time = time.time()

        out.release()
        print("화면 녹화가 종료되었습니다.")

def record_audio(stop_event, audio_filename, channels=2, rate=44100, frames_per_buffer=1024):
    """
    마이크 입력을 녹음하여 WAV 파일로 저장하는 함수입니다.
    
    Args:
        stop_event (threading.Event): 녹음 중지를 알리는 이벤트.
        audio_filename (str): 저장할 오디오 파일 이름 (예: "output_audio.wav").
        channels (int): 채널 수.
        rate (int): 샘플링 레이트 (Hz).
        frames_per_buffer (int): 버퍼 크기.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=frames_per_buffer)
    frames = []
    print("오디오 녹음을 시작합니다...")
    while not stop_event.is_set():
        # exception_on_overflow=False로 설정하여 오버플로우 예외 방지
        data = stream.read(frames_per_buffer, exception_on_overflow=False)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(audio_filename, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(rate)
    wf.writeframes(b"".join(frames))
    wf.close()
    print("오디오 녹음이 종료되었습니다.")

def main():
    video_filename = "output_video.avi"
    audio_filename = "output_audio.wav"
    stop_event = threading.Event()

    # 별도의 스레드에서 화면 녹화와 오디오 녹음을 실행합니다.
    video_thread = threading.Thread(target=record_screen, args=(stop_event, video_filename))
    audio_thread = threading.Thread(target=record_audio, args=(stop_event, audio_filename))
    
    video_thread.start()
    audio_thread.start()
    
    print("녹화를 진행 중입니다. 중지하려면 Ctrl+C를 누르세요...")
    try:
        # 메인 스레드에서 대기
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
    print("\n두 파일을 하나로 합치려면 ffmpeg 등을 이용할 수 있습니다. 예:")
    print(f"  ffmpeg -y -i {video_filename} -i {audio_filename} -c:v copy -c:a aac output_merged.mp4")

if __name__ == "__main__":
    main()
