import sounddevice as sd
import soundfile as sf

# 녹음 설정
duration = 10      # 녹음 시간 (초)
fs = 48000         # 샘플링 레이트
channels = 2       # 채널 수

# 장치 목록 출력 (원하는 장치와 인덱스를 확인)
print(sd.query_devices())

# WASAPI 루프백 모드에서 사용할 장치 인덱스를 설정합니다.
# 여기서는 헤드폰(WH-1000XM4)의 WASAPI 장치인 인덱스 17을 사용합니다.
device_index = 17

# WASAPI 루프백 설정 추가 (sounddevice의 WasapiSettings 사용)
wasapi_settings = sd.WasapiSettings(loopback=True)

print("녹음 시작...")
# extra_settings 파라미터를 사용하여 루프백 모드 활성화
recording = sd.rec(int(duration * fs),
                   samplerate=fs,
                   channels=channels,
                   device=device_index,
                   extra_settings=wasapi_settings)
sd.wait()  # 녹음이 끝날 때까지 대기
print("녹음 완료.")

# 녹음 파일로 저장
sf.write('output.wav', recording, fs)
print("파일 저장: output.wav")
