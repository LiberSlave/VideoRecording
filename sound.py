import sounddevice as sd
import soundfile as sf

# 녹음 설정
duration = 5  # 녹음 시간 (초)
fs = 44100     # 샘플링 레이트
channels = 2   # 채널 수

# 장치 목록 출력: WASAPI 루프백 장치가 있는지 확인합니다.
print(sd.query_devices())

# WASAPI 루프백 모드에서 사용할 장치 인덱스를 설정합니다.
# (출력된 장치 목록에서 "Loopback"이 포함된 장치를 선택하세요)
loopback_device_index = 16  # 예시 인덱스 (실제 시스템에 맞게 변경)

# 녹음 시작 (WASAPI 루프백 장치 사용)
print("녹음 시작...")
recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels, device=loopback_device_index)
sd.wait()  # 녹음이 끝날 때까지 대기
print("녹음 완료.")

# 녹음 파일로 저장
sf.write('output.wav', recording, fs)
print("파일 저장: output.wav")
