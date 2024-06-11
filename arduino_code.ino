#include <SoftwareSerial.h>
#include <HuemonelabKit.h>

#define RL 10.0  // 로드 저항 값 (여기서는 10kΩ으로 가정)
#define MQ_SENSOR_PIN A0  // MQ-137 센서가 연결된 아날로그 핀

#define cool 7

float Ro = 10.0;  // 초기 Ro 값, 보정된 후 수정될 예정
const float m = -0.263;  // 계산된 기울기 값
const float b = 0.42;    // 계산된 절편 값

Stepper stepper(8, 9, 10, 11);

int coolcmd = 0;

// SoftwareSerial 설정 (블루투스 모듈이 연결된 핀)
SoftwareSerial BTSerial(3, 4); // RX, TX

void setup() {
  Serial.begin(9600);
  BTSerial.begin(9600); // 블루투스 시리얼 통신 초기화
  pinMode(cool, OUTPUT);
  
  stepper.setSpeed(15);
  stepper.setDir(1);
  
  Serial.println("Calibrating...");
  Ro = calibrateSensor();  // 센서 보정
  Serial.print("Calibration is done. Ro = ");
  Serial.print(Ro);
  Serial.println(" kohm");

  // 맨처음 실행을 위한 부분 
  float VRL = analogRead(MQ_SENSOR_PIN) * (5.0 / 1023.0);  // 아날로그 값을 전압으로 변환
  float RS = ((5.0 * RL) / VRL) - RL;  // Rs 값 계산
  float ratio = RS / Ro;  // Rs/Ro 비율 계산
  float ppm = calculatePPM(ratio);  // ppm 계산

  BTSerial.print("MQ-137 bluetooth_Reading: ");
  BTSerial.print(ppm);
  BTSerial.print(" ppm, ");
  BTSerial.print(VRL);
  BTSerial.println(" V");
}

void loop() {
  char flag = '0';
  if(BTSerial.available()){
    flag = BTSerial.read();
    Serial.write(flag);
  }
  
  if(flag == '1'){
    coolcmd = 1;
    digitalWrite(cool, coolcmd);

    stepper.step(2048);

    stepper.setDir(0);

    stepper.step(2048);
    stepper.setDir(1);
    delay(1000);
  }else if(flag =='2'){
    coolcmd = 0;
    digitalWrite(cool, coolcmd);
    delay(1000);
  }
  
  float VRL = analogRead(MQ_SENSOR_PIN) * (5.0 / 1023.0);  // 아날로그 값을 전압으로 변환
  float RS = ((5.0 * RL) / VRL) - RL;  // Rs 값 계산
  float ratio = RS / Ro;  // Rs/Ro 비율 계산
  float ppm = calculatePPM(ratio);  // ppm 계산

  // 결과 출력 (시리얼 모니터)
//  Serial.print("MQ-137 Reading: ");
//  Serial.print(ppm);
//  Serial.print(" ppm, ");
//  Serial.print(VRL);
//  Serial.println(" V");

  // 결과 출력 (블루투스)
  BTSerial.print("MQ-137 bluetooth_Reading: ");
  BTSerial.print(ppm);
  BTSerial.print(" ppm, ");
  BTSerial.print(VRL);
  BTSerial.println(" V");

//  Serial.write(BTSerial.read());
//  Serial.println();

//  delay(2000); // firebase 요금 폭탄 방지
  delay(1000);
}

// 센서 보정 함수
float calibrateSensor() {
  int calibrationSampleTimes = 50;  // 보정을 위한 샘플 수
  float val = 0;

  for (int i = 0; i < calibrationSampleTimes; i++) {
    val += ((5.0 * RL) / (analogRead(MQ_SENSOR_PIN) * (5.0 / 1023.0))) - RL;
    delay(500);
  }

  val = val / calibrationSampleTimes;  // 평균 값 계산
  val = val / 1.67;  // 공기 중 Rs/Ro 비율을 1.67로 가정

  return val;  // 보정된 Ro 값 반환
}

// Rs/Ro 비율을 ppm으로 변환하는 함수
float calculatePPM(float ratio) {
  return pow(10, ((log10(ratio) - b) / m));
}