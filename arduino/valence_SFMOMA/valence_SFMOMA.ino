// Motor Speed Calibrator For Tauba Auerbach by Phillip David Stearns

// Libraries
#include <ArduinoJson.h>
#include <TimerOne.h> // including the TimerOne library for getting accurate speed readings
#include <DualG2HighPowerMotorShield.h>

// KEYWORDS FOR STATE MACHINE
#define CALIBRATE   0 //  pause and allow for mid routine adjustments
#define OPEN        1 //  move to targetOpen
#define OPEN_HOLD   2 //  hold on targetOpen
#define CLOSE       3 //  move to targetClosed
#define CLOSE_HOLD  4 //  hold on targetClosed
#define STARTUP     5 //  run EZO-PMP until wires are coated

// Interrupt pin numbers for Motor Encoders
#define M1_ENC1_IRQ_PIN 5 //18
#define M1_ENC2_IRQ_PIN 4 //19
#define M2_ENC1_IRQ_PIN 3 //20
#define M2_ENC2_IRQ_PIN 2 //21

// Physical pin numbers for Motor Encoders
#define M1_ENC1_PIN 18 // yellow
#define M1_ENC2_PIN 19 // white
#define M2_ENC1_PIN 20 // yellow
#define M2_ENC2_PIN 21 // white

// DualG2 Board
DualG2HighPowerMotorShield18v22 mDriver;

String serialReceived = "";

int sigmoidFunction = 2;
int machineState = STARTUP;
int lastMachineState = CALIBRATE;

volatile int mPositions[] = { 0, 0 };
volatile float mSpeeds[] = { 0, 0 };
int mPositionOffsets[] = { 0, 0 };
int mPositionsLast[] = { 0, 0 };

boolean isOpen = false;
boolean isClosed = false;

unsigned long openDuration = 15000; // the amount of time the movement should take
unsigned long openHoldDuration = 15000; // duration to hold open in ms
unsigned long closeDuration = 12500; // the amount of time the movement should take
unsigned long closeHoldDuration = 17500; // duration to hold open in ms
unsigned long startupDuration = 5000; // duration to hold open in ms (was 35000)

// control variables
const float stepAngle = 1.0 / 4200.0;
boolean moveMotors = true;

// variables for timing
unsigned long tCurrent = 0;
unsigned long tInitial = 0; // initial time when movement was started
unsigned long tDuration = 0; // the amount of time the movement should take
unsigned long tFinal = 0; // the time relative to initial time that the movement should complete

// Position Variables
int target = 0;
int targetOpen = 2550;
int targetClosed = 0;

// Power Variables
float powerScalar = 2.0;
float powerEasing = 1.0;
int targetWindow = 3; // +/- window for movement cutoff
int powerLimit = 480; // +/- maximum power sent to motors
float powerCutoff = 25; // +/- window for power cutoff
float speedCutoff = 0.01; // +/- window for speed cutoff

//////////////////////////////////////////////////////////////////
// ISRs
//
// encoder states are captured on interrupt pins
// these functions determine how they're treated
// read the value of the interrupt pins directly from PORTD registers
// if high compare to value of m1Enc2
// if m1Enc2 is high, set m1Dir = false, else true
// if m1Dir is true, m1Pos++, else m1Pos--

// motor 1 encoder pin 1
void m1Enc1() {
  if (digitalRead(M1_ENC1_PIN) != digitalRead(M1_ENC2_PIN)) {
    mPositions[0]--;
  } else {
    mPositions[0]++;
  }
}

// motor 2 encoder pin 1
void m2Enc1() {
  if (digitalRead(M2_ENC1_PIN) != digitalRead(M2_ENC2_PIN)) {
    mPositions[1]++;
  } else {
    mPositions[1]--;
  }
}

void calcMotorSpeeds() {
  for (int i = 0; i < 2; i++) {
    mSpeeds[i] = stepAngle * float(mPositions[i] - mPositionsLast[i]) * 10.0;
    mPositionsLast[i] = mPositions[i];
  }
}

//////////////////////////////////////////////////////////////////
// Progress percentage 0.0-1.0

float progress() {
  return float(tCurrent - tInitial) / float(tDuration);
}

//////////////////////////////////////////////////////////////////
// Sigmoid motion smoothing functions

float sigmoid(float _value, int _function) {
  _value = constrain(_value, 0.0, 1.0);
  switch (_function) {
    case 0: // natural log
      return 1 / ( 1 + pow(M_E, -(12 * _value - 6)));
      break;
    case 1: // hyperbolic tan
      return 0.5 * tanh((2 * PI * _value) - PI) + 0.5;
      break;
    case 2: // sine squared
      return pow(sin(0.5 * PI * _value), 2);
      break;
    default:
      return 0.0;
      break;
  }
}

//////////////////////////////////////////////////////////////////
// clearPositionFlags()
//
void clearPositionFlags() {
  isOpen = false;
  isClosed = false;
}

//////////////////////////////////////////////////////////////////
// MOTION CONTROL FUNCTIONS
// stopOnFault()

void stopOnFault() {
  if (mDriver.getM1Fault() || mDriver.getM2Fault()) {
    mDriver.disableDrivers();
    while (1) continue;
  }
}

//////////////////////////////////////////////////////////////////
// ease()

float ease(float _val, float _target, float _ease) {
  return _ease * (_target - _val);
}

//////////////////////////////////////////////////////////////////
//  moveToTarget()

void moveToTarget(int _target) {
  float mPower[] = { 0.0, 0.0 };
  float distance = 0.0;
  float force = 0.0;
  for (int i = 0 ; i < 2 ; i++) {
    distance = _target - (mPositions[i] + mPositionOffsets[i]);
    force = -powerScalar * distance;
    mPower[i] += ease(mPower[i], force, powerEasing);
    mPower[i] = constrain(mPower[i], -powerLimit, powerLimit);
    if (isClosed || isOpen) {
      if ((abs(mPower[i]) < powerCutoff) && (abs(mSpeeds[i]) < speedCutoff) ) mPower[i] = 0;
    }
  }
  mDriver.setSpeeds(mPower[0], mPower[1]);
  stopOnFault();
}

//////////////////////////////////////////////////////////////////
// stateMachine()

void stateMachine() {

  tCurrent = millis();

  switch (machineState) {
    case CALIBRATE: // calibration
      break;
    case OPEN: // open
      if (tCurrent >= tFinal) {
        isOpen = true;
      }
      if (isOpen) {
        tInitial = tCurrent;
        machineState = OPEN_HOLD;
      } else {
        target = int(sigmoid(progress(), sigmoidFunction) * float(targetOpen - targetClosed));
        clearPositionFlags();
      }
      break;
    case OPEN_HOLD: // holding open
      if ( (unsigned long) (tCurrent - tInitial) > openHoldDuration) {
        tInitial = tCurrent;
        tDuration = closeDuration;
        tFinal = tInitial + tDuration;
        machineState = CLOSE;
        clearPositionFlags();
      } else {
        target = targetOpen;
      }
      break;
    case CLOSE: // close
      if (tCurrent >= tFinal) {
        isClosed = true;
      }
      if (isClosed) {
        tInitial = tCurrent;
        machineState = CLOSE_HOLD;
      } else {
        target = int((1 - sigmoid(progress(), sigmoidFunction)) * float(targetOpen - targetClosed));
        clearPositionFlags();
      }
      break;
    case CLOSE_HOLD: // holding closed
      if ( (unsigned long) (tCurrent - tInitial) > closeHoldDuration) {
        tInitial = tCurrent;
        tDuration = openDuration;
        tFinal = tInitial + tDuration;
        machineState = OPEN;
        clearPositionFlags();
      } else {
        target = targetClosed;
      }
      break;
    case 5: // startup
      if ( (unsigned long) (tCurrent - tInitial) > startupDuration) {
        tInitial = tCurrent;
        tDuration = openDuration;
        tFinal = tInitial + tDuration;
        machineState = OPEN;
        clearPositionFlags();
      }
      break;
  }
}
//////////////////////////////////////////////////////////////////
// executeButtonAction()
// REWORK: for compatibility with serial control updates

//void executeButtonAction(int _button) {
//
//  if (machineState == CALIBRATE) { // if in calibration mode, buttons have these functions
//    switch (_button) {
//      case 0: // BUTTON 01 - decrease position by ~1 degree
//        m1PosOffset -= 11;
//        break;
//
//      case 1:  // BUTTON 02 - increase position by ~1 degree
//        m1PosOffset += 11;
//        break;
//
//      case 2: // BUTTON 03 - decrease position by ~10 degrees
//        m2PosOffset -= 11;
//        break;
//
//      case 3: // BUTTON 04 - increase position by ~10 degrees
//        m2PosOffset += 11;
//        break;
//
//      case 4: // BUTTON 05 - set open position
//        targetOpen = target;
//        break;
//
//      case 5: // BUTTON 06 - reset open position
//        targetOpen = initTargetOpen;
//        break;
//
//      case 6: // set close
//        targetClosed = target;
//        break;
//
//      case 7: // reset close
//        targetClosed = initTargetClose;
//        break;
//
//      case 8: // increase speed
//        //target = targetOpen;
//        break;
//
//      case 9: // decrease speed
//        //target = targetClosed;
//        break;
//
//      case 10: // reset speed
//        target -= 110;
//        break;
//
//      case 11: // pause
//        target += 110;
//        break;
//
//      case 12: // pump rate = startupFlow
//        //        setFlowRate(startupFlow);
//        break;
//
//      case 13: // pump rate = runFlow
//        //        setFlowRate(runFlow);
//        break;
//
//      case 14: // pause / resume pump
//        //        pausePump();
//        break;
//
//      case 15: //
//        machineState = lastMachineState;
//        break;
//    }
//  } else { // otherwise the machine is in run mode and has these functions
//    switch (_button) {
//      case 0: // BUTTON 01 - set state to Open
//        currentTime = millis();
//        ti = currentTime;
//        dT = 5000;
//        tf = ti + dT;
//        tp = 0;
//        machineState = OPEN;
//        clearPositionFlags();
//        break;
//
//      case 1:  // BUTTON 02 - set state to Close
//        currentTime = millis();
//        ti = currentTime;
//        dT = 5000;
//        tf = ti + dT;
//        tp = 0;
//        machineState = CLOSE;
//        clearPositionFlags();
//        break;
//
//      case 2: // BUTTON 03 - set state to Startup
//        machineState = STARTUP;
//        //        setFlowRate(startupFlow);
//        clearPositionFlags();
//        break;
//
//      case 3: // BUTTON 04 - enter calibration mode
//        lastMachineState = machineState;
//        machineState = CALIBRATE;
//        clearPositionFlags();
//        break;
//    }
//  }
//}

//////////////////////////////////////////////////////////////////
// Json stuff

void applySettings(JsonVariant _set) {
  DynamicJsonDocument debug(2048);
  if (_set["sigmoidFunction"] ) sigmoidFunction = _set["sigmoidFunction"];
  if (_set["machineState"]) machineState = _set["machineState"];
  if (_set["lastMachineState"]) lastMachineState = _set["lastMachineState"];
  if (_set["mPositionOffsets"]) {
    JsonArray offsets = debug.createNestedArray("mPositionOffsets");
    offsets.add(_set["mPositionOffsets"][0]);
    offsets.add(_set["mPositionOffsets"][1]);
  }
  if (_set["isOpen"]) isOpen = _set["isOpen"];
  if (_set["isClosed"]) isClosed = _set["isClosed"];
  if (_set["moveMotors"]) moveMotors = _set["moveMotors"];
  if (_set["openDuration"]) openDuration = _set["openDuration"];
  if (_set["openHoldDuration"]) openHoldDuration = _set["openHoldDuration"];
  if (_set["closeDuration"]) closeDuration = _set["closeDuration"];
  if (_set["closeHoldDuration"]) closeHoldDuration = _set["closeHoldDuration"];
  if (_set["startupDuration"]) startupDuration = _set["startupDuration"];
  if (_set["target"]) target = _set["target"];
  if (_set["targetOpen"]) targetOpen = _set["targetOpen"];
  if (_set["targetClosed"]) targetClosed = _set["targetClosed"];
  if (_set["powerScalar"]) powerScalar = _set["powerScalar"];
  if (_set["powerEasing"]) powerEasing = _set["powerEasing"];
  if (_set["targetWindow"]) targetWindow = _set["targetWindow"];
  if (_set["powerLimit"]) powerLimit = _set["powerLimit"];
  if (_set["powerCutoff"]) powerCutoff = _set["powerCutoff"];
  if (_set["speedCutoff"]) speedCutoff = _set["speedCutoff"];
}

void buildSnapshot(String _list[], int _size) {
  DynamicJsonDocument snapshot(1024);
  for (int i = 0 ; i < _size; i++) {
    String theKey = _list[i];
    if (theKey == "sigmoidFunction" ) {
      snapshot["sigmoidFunction"] = sigmoidFunction;
    } else if (theKey == "machineState") {
      snapshot["machineState"] = machineState;
    } else if (theKey == "lastMachineState") {
      snapshot["lastMachineState"] = lastMachineState;
    } else if (theKey == "mPositionOffsets") {
      JsonArray offsets = snapshot.createNestedArray("mPositionOffsets");
      offsets.add(mPositionOffsets[0]);
      offsets.add(mPositionOffsets[1]);
    } else if (theKey == "isOpen") {
      snapshot["isOpen"] = isOpen;
    } else if (theKey == "isClosed") {
      snapshot["isClosed"] = isClosed;
    } else if (theKey == "moveMotors") {
      snapshot["moveMotors"] = moveMotors;
    } else if (theKey == "openDuration") {
      snapshot["openDuration"] = openDuration;
    } else if (theKey == "openHoldDuration") {
      snapshot["openHoldDuration"] = openHoldDuration;
    } else if (theKey == "closeDuration") {
      snapshot["closeDuration"] = closeDuration;
    } else if (theKey == "closeHoldDuration") {
      snapshot["closeHoldDuration"] = closeHoldDuration;
    } else if (theKey == "startupDuration") {
      snapshot["startupDuration"] = startupDuration;
    } else if (theKey == "target") {
      snapshot["target"] = target;
    } else if (theKey == "targetOpen") {
      snapshot["targetOpen"] = targetOpen;
    } else if (theKey == "targetClosed") {
      snapshot["targetClosed"] = targetClosed;
    } else if (theKey == "powerScalar") {
      snapshot["powerScalar"] = powerScalar;
    } else if (theKey == "powerEasing") {
      snapshot["powerEasing"] = powerEasing;
    } else if (theKey == "targetWindow") {
      snapshot["targetWindow"] = targetWindow;
    } else if (theKey == "powerLimit") {
      snapshot["powerLimit"] = powerLimit;
    } else if (theKey == "powerCutoff") {
      snapshot["powerCutoff"] = powerCutoff;
    } else if (theKey == "speedCutoff") {
      snapshot["speedCutoff"] = speedCutoff;
    } else if (theKey == "mPositions") {
      JsonArray positions = snapshot.createNestedArray("mPositions");
      positions.add(mPositions[0]);
      positions.add(mPositions[1]);
    } else if (theKey == "mSpeeds") {
      JsonArray speeds = snapshot.createNestedArray("mSpeeds");
      speeds.add(mPositions[0]);
      speeds.add(mPositions[1]);
    } else if (theKey == "tCurrent") {
      snapshot["tCurrent"] = tCurrent;
    } else if (theKey == "tInitial") {
      snapshot["tInitial"] = tInitial;
    } else if (theKey == "tDuration") {
      snapshot["tDuration"] = tDuration;
    } else if (theKey == "tFinal") {
      snapshot["tFinal"] = tFinal;
    } else {
      snapshot[theKey] = "not found";
    }
  }
  serializeJson(snapshot, Serial);
  Serial.println();
}

void sendSnapshot() {
  DynamicJsonDocument snapshot(2048);
  snapshot["sigmoidFunction"] = sigmoidFunction;
  snapshot["machineState"] = machineState;
  snapshot["lastMachineState"] = lastMachineState;
  JsonArray offsets = snapshot.createNestedArray("mPositionOffsets");
  offsets.add(mPositionOffsets[0]);
  offsets.add(mPositionOffsets[1]);
  snapshot["isOpen"] = isOpen;
  snapshot["isClosed"] = isClosed;
  snapshot["moveMotors"] = moveMotors;
  snapshot["openDuration"] = openDuration;
  snapshot["openHoldDuration"] = openHoldDuration;
  snapshot["closeDuration"] = closeDuration;
  snapshot["closeHoldDuration"] = closeHoldDuration;
  snapshot["startupDuration"] = startupDuration;
  snapshot["target"] = target;
  snapshot["targetOpen"] = targetOpen;
  snapshot["targetClosed"] = targetClosed;
  snapshot["powerScalar"] = powerScalar;
  snapshot["powerEasing"] = powerEasing;
  snapshot["targetWindow"] = targetWindow;
  snapshot["powerLimit"] = powerLimit;
  snapshot["powerCutoff"] = powerCutoff;
  snapshot["speedCutoff"] = speedCutoff;
  JsonArray positions = snapshot.createNestedArray("mPositions");
  positions.add(mPositions[0]);
  positions.add(mPositions[1]);
  JsonArray speeds = snapshot.createNestedArray("mSpeeds");
  speeds.add(mSpeeds[0]);
  speeds.add(mSpeeds[1]);
  snapshot["tCurrent"] = tCurrent;
  snapshot["tInitial"] = tInitial; // initial time when movement was started
  snapshot["tDuration"] = tDuration; // the amount of time the movement should take
  snapshot["tFinal"] = tFinal; // the time relative to initial time that the movement should complete
  serializeJson(snapshot, Serial);
  Serial.println();
}

//////////////////////////////////////////////////////////////////
// Serial stuff

void parseSerial() {
  DynamicJsonDocument received(2048);
  DeserializationError error = deserializeJson(received, serialReceived);
  // Test if parsing succeeds.
  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return;
  } else {
    if (received["get"]) {
      if (received["get"] == "all") {
        sendSnapshot();
      } else {
        String list[32];
        int size = copyArray(received["get"], list);
        buildSnapshot(list, size);
      }
    } else if (received["set"]) {
      JsonVariant settings = received["set"].as<JsonVariant>();
      applySettings(settings);
    } else {
      DynamicJsonDocument error(512);
      error["error"] = "Unknown request";
      error["request"] = received[0];
      serializeJson(error, Serial);
      Serial.println();
    }
  }
}

void serialEvent() {
  while (Serial.available()) {
    serialReceived = Serial.readStringUntil('\n');
    parseSerial();
    serialReceived = "";
  }
}

//////////////////////////////////////////////////////////////////
// setup()

void setup() {
  // TimerOne SETUP for regular sampling of speed
  Timer1.initialize(1e5); // period in micro seconds (1e5 = 100ms)
  Timer1.attachInterrupt(calcMotorSpeeds);

  // DUAL G2 SETUP
  // Interrupt Pins
  pinMode(M1_ENC1_PIN, INPUT_PULLUP);
  pinMode(M1_ENC2_PIN, INPUT_PULLUP);
  pinMode(M2_ENC1_PIN, INPUT_PULLUP);
  pinMode(M2_ENC2_PIN, INPUT_PULLUP);

  mDriver.init();
  mDriver.calibrateCurrentOffsets();
  delay(1000);

  // Attaching Interrupt Pins to ISR functions to counter encoder changes
  attachInterrupt(M1_ENC1_IRQ_PIN, m1Enc1, CHANGE); // connect encoder to pin 18
  attachInterrupt(M2_ENC1_IRQ_PIN, m2Enc1, CHANGE); // connect encoder to pin 20

  // Uncomment to flip a motor's direction:
  mDriver.flipM1(true);
  //mDriver.flipM2(true);

  // Establish Serial Communication with Arduino
  Serial.begin(115200);
  while (!Serial) continue; // wait for serial port to connect.
  Serial.setTimeout(100);
  DynamicJsonDocument message(64);
  message["message"] = "Valence by Tauba Auerbach.";
  serializeJson(message, Serial);
  Serial.println();
  tInitial = millis();
}

//////////////////////////////////////////////////////////////////
// loop()

void loop() {
  stateMachine();
  if (moveMotors) moveToTarget(target);
}
