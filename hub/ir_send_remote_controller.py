from mindstorms.control import wait_for_seconds
import hub

class IR:
    # 适配zjiot红外学习模块。zjiot.taobao.com
    def __init__(self, uart) -> None:
        self.platform = None
        if hasattr(uart, "baud"):# LEGO HUB
            uart.baud(115200)
            self.platform = "lego"
        else:
            uart.__init__(115200)
        self.uart = uart

    def _sleep(self, sec):
        if self.platform == "lego":
            wait_for_seconds(sec)
        else:
            time.sleep_ms(sec*1000)


    def _send(self, msg):
        if hasattr(self.uart, "baud"):# LEGO HUB
            self.uart.write(msg)
        else:# ESP32
            self.uart.send(msg)

    def _read_all(self):
        if hasattr(self.uart, "baud"):# LEGO HUB
            return self.uart.read(512)
        else:# ESP32
            return self.uart.read_all()

    def wait_for_receive(self, channel=0):# 响应通道号0-6，默认0
        cmd = bytes(b'\x68\x08\x00\xFF\x10') + \
            bytes([channel]) + bytes([15+channel]) + bytes(b'\x16')
        success_msg = bytes(b'\x68\x0A\x00\x00\x02\x80') + bytes(
            [channel]) + bytes(b'\x00') + bytes([130+channel]) + bytes(b'\x16')
        print(cmd)
        print(success_msg)
        self._send(cmd)# 激活学习模式
        print('Waiting for remote-contrller...')
        still_waiting = True
        code = None
        while still_waiting:
            self._sleep(0.1)
            rtn = self._read_all()
            if rtn == b'':
                continue
            elif rtn == b'\x68\x08\x00\x00\x01\x00\x01\x16':# 激活学习模式的应答 68 08 00 00 01 00 01 16
                continue
            elif rtn == b'\x68\x08\x00\x00\x01\x01\x02\x16':# 激活学习模式时繁忙错误的应答 68 08 00 00 01 01 02 16
                continue
            elif rtn == success_msg:# 学习成功。上报帧格式：68 0A 00 00 02 80 00 00 82 16
                print('Get remote-contrller message')
                return self._get_study_code()
            else:
                print('Unexpected code', rtn)
                self._send(cmd)# 重新激活学习模式

    def _get_study_code(self):
        self._send(b'\x68\x08\x00\xff\x18\x00\x17\x16')# 读取学习到的遥控码
        self._sleep(0.3)
        return self._read_all()

    def transport(self):
        pass

    def transport_internal_code(self, channel):# 内码发射，通道号0-6
        self._send(bytes(b'\x68\x08\x00\xFF\x12') +
                bytes([channel]) + bytes([17+channel]) + bytes(b'\x16'))






uart = hub.port.F # p5接对方RXD，p6接对方TXD
uart.mode(hub.port.MODE_FULL_DUPLEX)
wait_for_seconds(1)# wait for all duplex methods to appear
uart.baud(115200)

ir = IR(uart)
# ir.wait_for_receive(0)
# wait_for_seconds(3)
# ir.wait_for_receive(1)

from mindstorms import MSHub
hub = MSHub()
while True:
    wait_for_seconds(0.1)
    if hub.left_button.is_pressed():
        print('send ir-l')
        ir.transport_internal_code(0)
        wait_for_seconds(0.1)
    if hub.right_button.is_pressed():
        print('send ir-r')
        ir.transport_internal_code(1)
        wait_for_seconds(0.1)


