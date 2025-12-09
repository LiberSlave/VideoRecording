import cv2
import numpy as np
import mss
import threading
import time

def record_screen(stop_event, video_filename, fps=20.0, monitor_index=1):
    """
    화면을 캡처하여 지정한 파일로 저장하는 함수입니다.
    
    Args:
        stop_event (threading.Event): 녹화를 중지시키기 위한 이벤트 객체.
        video_filename (str): 저장할 영상 파일 이름 (예: "output_video.avi").
        fps (float): 초당 프레임 수.
        monitor_index (int): 캡처할 모니터 번호 (mss 모듈에서 1부터 시작).
    """
    with mss.mss() as sct:
        # 지정한 모니터의 정보 가져오기
        monitor = sct.monitors[monitor_index]
        width = monitor["width"]
        height = monitor["height"]
        
        # OpenCV VideoWriter 설정 (XVID 코덱 사용)
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
        
        print("화면 녹화를 시작합니다...")
        last_time = time.time()
        while not stop_event.is_set():
            # 화면 캡처
            img = np.array(sct.grab(monitor))
            # BGRA에서 BGR로 변환 (OpenCV에서 사용)
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            
            # FPS 유지하기 위한 딜레이
            elapsed = time.time() - last_time
            sleep_time = max(0, 1 / fps - elapsed)
            time.sleep(sleep_time)
            last_time = time.time()
        
        out.release()
        print("화면 녹화가 종료되었습니다.")

def main():
    video_filename = "output_video.avi"  # 저장할 영상 파일 이름
    stop_event = threading.Event()         # 녹화 중지를 위한 이벤트 객체

    # 화면 녹화 스레드 생성 및 시작
    video_thread = threading.Thread(target=record_screen, args=(stop_event, video_filename))
    video_thread.start()
    
    print("녹화를 진행 중입니다. 중지하려면 Ctrl+C를 누르세요...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n녹화를 중지합니다...")
        stop_event.set()
    
    video_thread.join()
    
    print("녹화가 완료되었습니다.")
    print(f"영상 파일: {video_filename}")

if __name__ == "__main__":
    main()
