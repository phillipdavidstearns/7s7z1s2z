/* Dual Quadrature Rotary Decoder
   Uses Pin Change interrupts of the Atmega328p
   Encoder 1 - A -> D8, B -> D9
   Encoder 2 - A -> ADC0, B -> ADC1
   refs:
   http://gammon.com.au/interrupts
*/

#define ENC1A_PIN 2
#define ENC1B_PIN 4
#define ENC2A_PIN 3
#define ENC2B_PIN 5

// motor position variables
volatile int enc1Count = 0;
volatile int enc2Count = 0;
int position1 = 0;
int position2 = 0;
int reg1 = 0;
int reg2 = 0;

// serial poll timing variables
long currentTime = 0;
long lastTime = 0;
long triggerTime = 10; // every 10ms

//////////////////////////////////////////////////////////////////////////////
// External Interrupt ISRs

ISR(INT0_vect) { // attached to pin2
  reg1 = PIND;
  if ( ((reg1 >> ENC1A_PIN) & 1) == ((reg1 >> ENC1B_PIN) & 1)) {
    --enc1Count;
  } else {
    ++enc1Count;
  }
}

ISR(INT1_vect) { // attached to pin3
  reg2 = PIND;
  if ( ((reg2 >> ENC2A_PIN) & 1) == ((reg2 >> ENC2B_PIN) & 1)) {
    --enc2Count;
  } else {
    ++enc2Count;
  }
}

//////////////////////////////////////////////////////////////////////////////
// Serial Communication

void sendCounts() {
  cli();
  position1=enc1Count;
  position2=enc2Count;
  sei();
  Serial.print(position1);
  Serial.print('|');
  Serial.println(position2);
}

//////////////////////////////////////////////////////////////////////////////
// Setup

void setup() {
  EICRA |= 0b00000101; // set INT0 and INT1 to respond to any voltage changes
  EIMSK |= 0b00000011; // enable INT0 and INT1

  //  according to pololu, the encoders don't need pullup resistors
  pinMode(ENC1A_PIN, INPUT_PULLUP);
  pinMode(ENC1B_PIN, INPUT_PULLUP);
  pinMode(ENC2A_PIN, INPUT_PULLUP);
  pinMode(ENC2B_PIN, INPUT_PULLUP);

  Serial.setTimeout(1);
  Serial.begin(115200);   // start serial for output for debugging
}

//////////////////////////////////////////////////////////////////////////////
// Loop

void loop() {
  currentTime = millis();
  if (currentTime - lastTime >= triggerTime) {
    // if we receive ANYTHING on the serial port, clear the counts
    // never be not sending
    if(Serial.available() > 0){
      while(Serial.read() != -1){
      }
      cli();
      enc1Count = 0;
      enc2Count = 0;
      sei();
    }
    sendCounts();
    lastTime = currentTime;
  }
}
