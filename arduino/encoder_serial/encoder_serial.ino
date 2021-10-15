#include <avr/io.h>
#include <avr/interrupt.h>
#include <SoftwareSerial.h>

// pins definitions (PORTB addresses)
#define ENCA_PIN 2  // INT0 (dip8 pin 7)
#define ENCB_PIN 0  // (dip8 pin 5)
#define TX_PIN 3    // (dip8 pin 2)
#define RX_PIN 4    // (dip8 pin 3)

volatile long counter = 0;
volatile uint8_t lastState = 0; // used for debouncing encoder triggered interrupt pin

// setup the serial port
SoftwareSerial serial =  SoftwareSerial(RX_PIN, TX_PIN);

void setup() {
  // setup external interrupt INT0
  SREG |= 0b10000000; // enables interrupts
  MCUCR |= 0b00000001; // sets interupt to trigger on any logical change
  GIMSK |= 0b01000000; // enables INT0 interrupts

  // setup pin modes
  pinMode(ENCA_PIN, INPUT);
  pinMode(ENCB_PIN, INPUT);
  //  pinMode(RX_PIN, INPUT);
  //  pinMode(TX_PIN, OUTPUT);

  serial.begin(115200);
  lastState = (PINB >> ENCA_PIN) & 1; // gets the initial state of the encoder pins
}

void loop() {
  if (serial.available()) { // when serial data is in the buffer
    while (serial.available() > 0) { // loop through all data
      char d = serial.read() & 0b01111111; // read 1 byte
      if ( d == 'r' ) { // request for reset
        counter = 0; // set the counter to 0
        serial.println("ok");
      } else { // anything else sends the counter
        serial.print(counter);
      }
    }
  }
}

ISR(INT0_vect) { // pin change interrupt for INT0 on PB2, DIP8 pin 7
  // read the encoder pins
  volatile uint8_t encA = (PINB >> ENCA_PIN) & 1; //triggered the interrupt
  volatile uint8_t encB = (PINB >> ENCB_PIN) & 1;
  if ( encA != lastState) { // debounce
    lastState = encA;
    if (encA == encB) {
      --counter;
    } else {
      ++counter;
    }
  }
}
