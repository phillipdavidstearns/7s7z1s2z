/* Dual Quadrature Rotary Decoder
   Uses Pin Change interrupts of the Atmega328p
   Encoder 1 - A -> D8, B -> D9
   Encoder 2 - A -> ADC0, B -> ADC1
   I2C - SDA -> ADC4, SCL -> ADC5
   Code commented out is a working implementation of
   hardware interrupt pins INT0 and INT1
*/

// here incase we need to revert to using INT0 and INT1
//volatile long enc1Count = 0;
//volatile long enc2Count = 0;
//volatile boolean enc1ALast = 0;
//volatile boolean enc2ALast = 0;

// encoder variables
volatile long enc1Count = 0;
volatile long enc2Count = 0;
volatile int enc1LastState = 0;
volatile int enc2LastState = 0;
const int stateTable[] = { 0, 1, -1, 0, -1, 0, 0, 1, 1, 0, 0, -1, 0, -1, 1, 0 };

// serial read write variables
const uint8_t buffSize = 3;
char buff[buffSize];
char request = 0;
char device = 0;

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
// Serial Communication

void pollSerial(){
  if (Serial.available() >= 3) {
    uint8_t bytesRead = Serial.readBytesUntil('\n', buff, buffSize);
    if (bytesRead == 2) {
      request = buff[0];
      device = buff[1];
      if (request == 'g' && device == '0') {
        Serial.print(enc1Count);
        Serial.print('|');
        Serial.println(enc2Count);
      } else if (request == 'g' && device == '1') {
        Serial.println(enc1Count);
      } else if (request == 'g' && device == '2') {
        Serial.println(enc2Count);
      } else if (request == 'c' && device == '0') {
        enc1Count = 0;
        enc2Count = 0;
      } else if (request == 'c' && device == '1') {
        enc1Count = 0;
      } else if (request == 'c' && device == '2') {
        enc2Count = 0;
      } else {
        Serial.println("err!");
      }
    }
    // clear the buffer;
    for (int i = 0; i < buffSize; ++i) {
      buff[i] = 0;
    }
  }
}

//////////////////////////////////////////////////////////////////////////////
// Setup

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
  Serial.setTimeout(1);
  Serial.begin(115200);   // start serial for output for debugging

  // here in case we need to revert fo INT0 and INT1
  //  enc1ALast = (PIND >> ENC1A_PIN) & 1;
  //  enc2ALast = (PIND >> ENC2A_PIN) & 1;

  enc1LastState = (PINB & 1) << 1 | (( PINB >> 1 ) & 1); // PINB0 = D8, PINB1 = D9
  enc2LastState = (PINC & 1) << 1 | (( PINC >> 1 ) & 1); // PINC0 = ADC0, PINC1 = ADC1
}

//////////////////////////////////////////////////////////////////////////////
// Loop

void loop() {
  pollSerial();
}
