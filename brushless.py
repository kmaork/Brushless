from serial import Serial
from dataclasses import dataclass
from bitstring import Bits
from contextlib import contextmanager
import time


@dataclass
class FieldMetadata:
    length: int
    minimum: float
    maximum: float


@dataclass
class Field:
    value: float
    metadata: FieldMetadata

    def to_int(self):
        value = min(self.metadata.maximum, max(self.value, self.metadata.minimum))
        span = self.metadata.maximum - self.metadata.minimum
        magnitude = value - self.metadata.minimum
        ratio = ((1 << self.metadata.length) - 1) / span
        return int(magnitude * ratio)

    @classmethod
    def pack(cls, fields):
        bits = Bits()
        for field in fields:
            bits += Bits(length=field.metadata.length, uint=field.to_int())
        assert len(bits) % 8 == 0
        return bits.bytes


@dataclass
class AK606Config:
    POSITION = FieldMetadata(16, -95.5, 95.5)
    SPEED = FieldMetadata(12, -45, 45)
    TORQUE = FieldMetadata(12, -18, 18)  # -9, 9?
    KP = FieldMetadata(12, 0, 500)
    KD = FieldMetadata(12, 0, 5)

    position: float
    speed: float
    kp: float
    kd: float
    torque: float

    @property
    def can_data(self):
        return Field.pack([Field(self.position, self.POSITION),
                           Field(self.speed, self.SPEED),
                           Field(self.kp, self.KP),
                           Field(self.kd, self.KD),
                           Field(self.torque, self.TORQUE)])


class Motor:
    RLINK_PREFIX = bytes.fromhex('aaaf0fa1')
    STARTUP_RLINK_MESSAGE = bytes.fromhex('aaaf07a2a101a4')

    def __init__(self, serial, motor_id):
        self.serial = serial
        self.motor_id = motor_id

    @classmethod
    @contextmanager
    def connect(cls, port_name: str, motor_id=1, baud_rate=921600):
        with Serial(port=port_name, baudrate=baud_rate) as ser:
            ser.write(cls.STARTUP_RLINK_MESSAGE)
            ser.read(7)
            yield cls(ser, motor_id)

    @staticmethod
    def _calc_checksum(data: bytes):
        return (sum(data) & 0xff).to_bytes(1, 'big')

    def send_message(self, can_data):
        data = self.RLINK_PREFIX + can_data + self.motor_id.to_bytes(1, 'big') + b'\1'
        message = data + self._calc_checksum(data)
        self.serial.write(message)
        self.serial.read(11)

    def start(self):
        self.send_message(bytes.fromhex('fffffffffffffffc'))

    def stop(self):
        self.send_message(bytes.fromhex('fffffffffffffffd'))

    def reset(self):
        self.send_message(bytes.fromhex('fffffffffffffffe'))

    def set_position(self, position, kp=2, kd=0.2):
        self.send_message(AK606Config(position=position, speed=0, kp=kp, kd=kd, torque=0).can_data)

    def set_speed(self, speed, kd=0.5):
        self.send_message(AK606Config(position=0, speed=speed, kp=0, kd=kd, torque=0).can_data)

    def set_torque(self, torque, kd=0.2):
        self.send_message(AK606Config(position=0, speed=0, kp=0, kd=kd, torque=torque).can_data)


def demo(usb_port):
    with Motor.connect(usb_port) as motor:
        motor.start()
        time.sleep(1)
        motor.reset()
        time.sleep(1)
        for _ in range(2):
            motor.set_position(-10)
            time.sleep(1)
            motor.set_position(10)
            time.sleep(1)
        motor.set_speed(-2)
        time.sleep(3)
        motor.set_speed(-2)
        time.sleep(3)
        motor.stop()


if __name__ == '__main__':
    import sys

    demo(sys.argv[1])
