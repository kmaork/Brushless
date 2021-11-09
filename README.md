## Setup
- Run:
  ```bash
  pip install -r requirements.txt
  ```

## Usage
- Connect the RLink device to a USB port 
- Find the port name (On windows this could be done using device manager. This could be automated in the future)
- Run:
  ```bash
  python3 brushless.py YOUR_PORT_NAME
  ```

## Modification
Edit the function `demo` in `brushless.py` to change the demo. 

## Notes
- Another python script for controlling similar motors via direct CAN (without RLink):
  https://github.com/dfki-ric-underactuated-lab/mini-cheetah-tmotor-python-can/blob/main/src/motor_driver/canmotorlib.py