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
        monitor = sct.monitors[monitor_index]
        width = monitor["width"]
        height = monitor["height"]
        
        # OpenCV의 VideoWriter를 사용하여 영상 파일로 저장 (XVID 코덱 사용)
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
        
        print("화면 녹화를 시작합니다...")
        last_time = time.time()
        while not stop_event.is_set():
            # 지정된 모니터 전체를 캡처합니다.
            img = np.array(sct.grab(monitor))
            # mss는 BGRA 형식으로 캡처하므로, BGR로 변환합니다.
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            
            # FPS를 맞추기 위한 딜레이 처리
            elapsed = time.time() - last_time
            sleep_time = max(0, 1/fps - elapsed)
            time.sleep(sleep_time)
            last_time = time.time()
            
        out.release()
        print("화면 녹화가 종료되었습니다.")

def record_system_audio(stop_event, audio_filename, channels=2, rate=44100, frames_per_buffer=1024):
    """
    시스템(내부) 오디오를 녹음하여 WAV 파일로 저장하는 함수입니다.
    
    이 함수는 Windows WASAPI의 loopback 기능을 사용하여
    컴퓨터에서 출력되는 소리를 캡처합니다.
    
    Args:
        stop_event (threading.Event): 녹음 중지를 알리는 이벤트.
        audio_filename (str): 저장할 오디오 파일 이름 (예: "output_audio.wav").
        channels (int): 오디오 채널 수 (기본값: 2, 스테레오).
        rate (int): 샘플링 레이트 (Hz, 기본값: 44100).
        frames_per_buffer (int): 버퍼 크기.
    """
    p = pyaudio.PyAudio()
    
    # WASAPI 호스트 API 정보를 가져옵니다.
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    except Exception as e:
        print("WASAPI 호스트 API 정보를 가져올 수 없습니다:", e)
        p.terminate()
        return

    # 루프백(Loopback) 장치 탐색: 이름에 "loopback"이 포함된 장치를 찾습니다.
    loopback_device_index = None
    for i in range(p.get_device_count()):
        device = p.get_device_info_by_index(i)
        if device['hostApi'] == wasapi_info['index'] and device['maxInputChannels'] > 0:
            if "loopback" in device['name'].lower():
                loopback_device_index = i
                break

    if loopback_device_index is None:
        print("시스템 오디오를 녹음할 수 있는 루프백 장치를 찾을 수 없습니다.")
        p.terminate()
        return

    try:
        # WASAPI 루프백 모드로 오디오 스트림을 엽니다.
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=rate,
            input=True,
            frames_per_buffer=frames_per_buffer,
            input_device_index=loopback_device_index,
            as_loopback=True  # WASAPI 루프백 모드 활성화
        )
    except Exception as e:
        print("오디오 스트림을 열 수 없습니다:", e)
        p.terminate()
        return

    frames = []
    print("시스템 오디오 녹음을 시작합니다...")
    while not stop_event.is_set():
        try:
            # 버퍼 단위로 오디오 데이터를 읽어옵니다.
            data = stream.read(frames_per_buffer, exception_on_overflow=False)
            frames.append(data)
        except Exception as e:
            print("오디오 데이터 읽기 중 오류 발생:", e)
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    # 녹음된 오디오 데이터를 WAV 파일로 저장합니다.
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

    # 화면 녹화와 시스템 오디오 녹음을 별도의 스레드에서 실행합니다.
    video_thread = threading.Thread(target=record_screen, args=(stop_event, video_filename))
    audio_thread = threading.Thread(target=record_system_audio, args=(stop_event, audio_filename))
    
    video_thread.start()
    audio_thread.start()
    
    print("녹화를 진행 중입니다. 중지하려면 Ctrl+C를 누르세요...")
    try:
        # 메인 스레드는 무한 대기
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
