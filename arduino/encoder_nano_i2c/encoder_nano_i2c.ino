/* Dual Quadrature Rotary Decoder
   Uses Pin Change interrupts of the Atmega328p
   Encoder 1 - A -> D8, B -> D9
   Encoder 2 - A -> ADC0, B -> ADC1
   I2C - SDA -> ADC4, SCL -> ADC5
   Code commented out is a working implementation of
   hardware interrupt pins INT0 and INT1
*/

#include <Wire.h>

#define ADDRESS 0x10 // I2C bus address

// here incase we need to revert to using INT0 and INT1
//volatile long enc1Count = 0;
//volatile long enc2Count = 0;
//volatile boolean enc1ALast = 0;
//volatile boolean enc2ALast = 0;

volatile long enc1Count = 0;
volatile long enc2Count = 0;
volatile int enc1LastState = 0;
volatile int enc2LastState = 0;
const int stateTable[] = { 0, 1, -1, 0, -1, 0, 0, 1, 1, 0, 0, -1, 0, -1, 1, 0 };
volatile byte request = 0;
volatile byte device = 0;

// for debugging purposes
//const int interval = 100; //miliseconds
//int lastTime = 0;

void setup() {
  EICRA |= 0b00000101; // set INT0 and INT1 to respond to any voltage changes
  //  EIMSK |= 0b00000011; // enable INT0 and INT1
  PCICR |= 0b00000011; // enable pin change interrupts 0 and 1
  PCMSK0 = 0b00000011; // enable PCI00 (D8, PINB0) & PCI01 (D9, PINB1)
  PCMSK1 = 0b00000011; // enable PCI10 (ADC0, PINC0) & PCI11 (ADC1, PINC1)

  //  pinMode(ENC1A_PIN, INPUT_PULLUP);
  //  pinMode(ENC1B_PIN, INPUT_PULLUP);
  //  pinMode(ENC2A_PIN, INPUT_PULLUP);
  //  pinMode(ENC2B_PIN, INPUT_PULLUP);
  Wire.onReceive(onI2CReceive);     // register event
  Wire.onRequest(onI2CRequest);     // register event
  Wire.setClock(100000);
  Wire.begin(ADDRESS);  // join i2c bus with address #8
//  Serial.begin(9600);   // start serial for output for debugging
  clearWire();
  // here in case we need to revert fo INT0 and INT1
  //  enc1ALast = (PIND >> ENC1A_PIN) & 1;
  //  enc2ALast = (PIND >> ENC2A_PIN) & 1;

  enc1LastState = (PINB & 1) << 1 | (( PINB >> 1 ) & 1); // PINB0 = D8, PINB1 = D9
  enc2LastState = (PINC & 1) << 1 | (( PINC >> 1 ) & 1); // PINC0 = ADC0, PINC1 = ADC1
}

void loop() {
  // For debugging to the serial monitor
//  int currentTime = millis();
//  if (currentTime - lastTime >= interval) {
//    lastTime = currentTime;
//    Serial.print("request: ");
//    Serial.print(char(byte1));
//    Serial.print(" | device: ");
//    Serial.print(byte2);
//    Serial.println();
//  }
}

//////////////////////////////////////////////////////////////////////////////
// Pin Change Interrupt ISRs

ISR(PCINT0_vect) {
  // D8 = PINB0
  // D9 = PINB1
  volatile int enc1State = (PINB & 1) << 1 | (( PINB >> 1 ) & 1);
  volatile int stateCode = (enc1LastState << 2) | enc1State;
  volatile int encValue = stateTable[stateCode];
  if (encValue) {
    enc1LastState = enc1State;
    enc1Count += encValue;
  }
}

ISR(PCINT1_vect) {
  // ADC0 = PINC0
  // ADC1 = PINC1
  volatile int enc2State = (PINC & 1) << 1 | (( PINC >> 1 ) & 1);
  volatile int stateCode = (enc2LastState << 2) | enc2State;
  volatile int encValue = stateTable[stateCode];
  if (encValue) {
    enc2LastState = enc2State;
    enc2Count += encValue;
  }
}

//////////////////////////////////////////////////////////////////////////////
// External Interrupt ISRs

//ISR(INT0_vect) { // attached to pin2
//  volatile boolean enc1A = (PIND >> ENC1A_PIN) & 1; //triggered the interrupt
//  volatile boolean enc1B = (PIND >> ENC1B_PIN) & 1;
//  if ( enc1A != enc1ALast ) { // debounce
//    enc1ALast = enc1A;
//    if (enc1A == enc1B) {
//      ++enc1Count;
//    } else {
//      --enc1Count;
//    }
//  }
//}
//
//ISR(INT1_vect) { // attached to pin3
//  volatile boolean enc2A = (PIND >> ENC2A_PIN) & 1; //triggered the interrupt
//  volatile boolean enc2B = (PIND >> ENC2B_PIN) & 1;
//  if ( enc2A != enc2ALast ) { // debounce
//    enc2ALast = enc2A;
//    if (enc2A == enc2B) {
//      ++enc2Count;
//    } else {
//      --enc2Count;
//    }
//  }
//}

//////////////////////////////////////////////////////////////////////////////
// I2C Communication

int onI2CReceive(int qtyBytes) {
  // loop through all the data
  if (qtyBytes == 2) {
    volatile byte byte1 = Wire.read();
    volatile byte byte2 = Wire.read();
    if (( byte1 == 'g' || byte1 == 'c' ) && (byte2 == '1' || byte2 == '2')) {
      request = byte1;
      device = byte2;
    }
  } else {
    clearWire();
  }
  //  return 0;
}

void clearWire() {
  while (Wire.available() > 0) {
    Wire.read();
  }
}

void onI2CRequest() {
  switch (char(request)) {
    case 'g':
      if (char(device) == '1') {
        long count1 = enc1Count;
        uint8_t count[] = { (count1 >> 24) & 0xff,
                            (count1 >> 16) & 0xff,
                            (count1 >> 8) & 0xff,
                            count1 & 0xff
                          };
        Wire.write(count, 4);
      } else if (char(device) == '2') {
        long count2 = enc2Count;
        uint8_t count[] = { ( count2 >> 24 ) & 0xff,
                            ( count2 >> 16 ) & 0xff,
                            ( count2 >> 8 ) & 0xff,
                            count2 & 0xff
                          };
        Wire.write(count,4);
      }
      break;
    case 'c':
      if (char(device) == '1') {
        enc1Count = 0;
        Wire.write("c1ok",4);
      } else if (char(device) == '2') {
        enc2Count = 0;
        Wire.write("c2ok",4);
      }
      break;
    default:
      Wire.write("err!",4);
      break;
  }
  request = 0;
  device = 0;
}
