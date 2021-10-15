//#include <avr/io.h>
//#include <avr/interrupt.h>
#include <SoftwareSerial.h>

#define ENCA_PIN 5
#define ENCB_PIN 3

volatile uint8_t encLastValidState = 0;
volatile long counter = 0;

const int stateCodeTable[] = { 0, 1, -1, 0, -1, 0, 0, 1, 1, 0, 0, -1, 0, -1, 1, 0 };

uint8_t readEncPins() {
  return PB5 << 1 | PB3;
}

uint8_t getStateCode(uint8_t encState) {
  return (encLastValidState << 2) | ( encState & 3);
}

void setup() {
  SREG |= 0b10000000; // enables interrupts
  MCUCR |= 0b00000001; // sets interupt to trigger on any logical change
  GIMSK |= 0b00100000; // enables pinchange interrupts
  PCMSK |= 0b00101000; // enables pinchange interrupts on PB5 and PB3
  encLastValidState = readEncPins(); // gets the initial state of the encoder pins
}

void loop() {
  //silence is golden
}

ISR(PCINT0_vect) { //pin change interrupt
  // read current encoder pin states
  volatile uint8_t encCurrentState = readEncPins();
  // use encoded state to check if current state it valid
  volatile int tableValue = stateCodeTable[ getStateCode( encCurrentState ) ];
  // if yes save current state to last valid, and increment counter accordingly
  if ( tableValue ) {
    encLastValidState = encCurrentState;
    counter += tableValue;
  }
}
