#include <avr/io.h>
#include <avr/interrupt.h>
#include <TinyWire.h>

// encoder pins
#define ENCA_PIN 1
#define ENCB_PIN 3
#define ADDRESS 0x10 // I2C bus address, use 0x10 for M1 encoder, 0x11 for M2 encoder

volatile long counter = 0;
volatile uint8_t lastState = 0; // used for debouncing encoder triggered interrupt pin

void setup() {

  // setup pin modes
  pinMode(ENCA_PIN, INPUT_PULLUP);
  pinMode(ENCB_PIN, INPUT_PULLUP);
  //  pinMode(RX_PIN, INPUT);
  //  pinMode(TX_PIN, OUTPUT);

  // setup external interrupt INT0
  SREG |= 0b10000000; // enables interrupts
  MCUCR |= 0b00000001; // sets interupt to trigger on any logical change
  GIMSK |= 0b01000000; // enables INT0 interrupts
  
   // config TinyWire library for I2C slave functionality
  TinyWire.begin( ADDRESS );
  // sets callback for the event of a slave receive & request
  TinyWire.onReceive( onI2CReceive );
  TinyWire.onRequest( onI2CRequest );

  lastState = PB1; // gets the initial state of the encoder pins
}

void loop() {
  //  if (serial.available()){ // when serial data is in the buffer
  //    while (serial.available()>0){ // loop through all data
  //      byte data = serial.read(); // read 1 byte
  //      if ( data == 'r' ){ // request for read
  //        serial.println(counter); // send the counter value
  //      } else if ( data == 'c'){ // request for clear
  //        counter = 0; // set the counter to 0
  //      } else { // anything else fires back an error message
  //        serial.println("error");
  //      }
  //    }
  //  }
}

ISR(INT0_vect) { //pin change interrupt
  // read the encoder pins
  volatile boolean encA = PB2; //triggered the interrupt
  volatile boolean encB = PB3;
  if ( encA != lastState) { // debounce
    lastState = encA;
    if (encA == encB) {
      --counter;
    } else {
      ++counter;
    }
  }
}

//////////////////////////////////////////////////////////////////////////////
int onI2CReceive( int qtyBytes) {
  byte data = 0;
  // loop through all the data
  while (TinyWire.available() > 0) {
    //read first byte in the buffer
    data = TinyWire.read();
    if (data == 'g') { // "get" request, send counter value
      TinyWire.send(counter,4);
    } else if (data == 'c') { // "clear" request, clear the counter
      counter = 0;
      TinyWire.send('c');
    } else {
      // bad data
      TinyWire.send('e');
    }
  }
}

//////////////////////////////////////////////////////////////////////////////

void onI2CRequest() {
  // non-blocking acknowlegement
  TinyWire.send('b');
}
