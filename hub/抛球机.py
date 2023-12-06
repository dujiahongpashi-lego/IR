# 连线：
# 俯仰 电机E
# 乐高手指 电机F
# （同电机水平 不做编程）数显 电机D
# 开关 距离传感器A
# 信号 红外A
# 击球电机 不做编程
# 灯/颜色传感器 不做编程

MODE = "IR_MODE"# 'IR_MODE' / 'DISTANCE_MODE'

from mindstorms import DistanceSensor, Motor
from time import sleep_ms
from hub import button, port, display, Image

# 初始化器件端口
pitch_motor = Motor("E")
finger_motor = Motor("F")
digit_machine_motor = Motor("D")
#distance = DistanceSensor("A")
import hub

ir_sensor = hub.port.A
if MODE == "IR_MODE":
    ir_sensor.mode(hub.port.MODE_FULL_DUPLEX)
    sleep_ms(1000)# wait for all duplex methods to appear
    ir_sensor.baud(115200)


from mindstorms.control import wait_for_seconds


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
            time.sleep_ms(sec * 1000)

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
        cmd = (
            bytes(b"\x68\x08\x00\xFF\x10")
            + bytes([channel])
            + bytes([15 + channel])
            + bytes(b"\x16")
        )
        success_msg = (
            bytes(b"\x68\x0A\x00\x00\x02\x80")
            + bytes([channel])
            + bytes(b"\x00")
            + bytes([130 + channel])
            + bytes(b"\x16")
        )
        print(cmd)
        print(success_msg)
        self._send(cmd)# 激活学习模式
        print("Waiting for remote-contrller...")
        still_waiting = True
        code = None
        while still_waiting:
            self._sleep(0.1)
            rtn = self._read_all()
            if rtn == b"":
                continue
            elif (
                rtn == b"\x68\x08\x00\x00\x01\x00\x01\x16"
            ):# 激活学习模式的应答 68 08 00 00 01 00 01 16
                continue
            elif (
                rtn == b"\x68\x08\x00\x00\x01\x01\x02\x16"
            ):# 激活学习模式时繁忙错误的应答 68 08 00 00 01 01 02 16
                continue
            elif rtn == success_msg:# 学习成功。上报帧格式：68 0A 00 00 02 80 00 00 82 16
                print("Get remote-contrller message")
                return self._get_study_code()
            else:
                print("Unexpected code", rtn)
                self._send(cmd)# 重新激活学习模式

    def _get_study_code(self):
        self._send(b"\x68\x08\x00\xff\x18\x00\x17\x16")# 读取学习到的遥控码
        self._sleep(0.3)
        return self._read_all()

    def transport(self):
        pass

    def transport_internal_code(self, channel):# 内码发射，通道号0-6
        self._send(
            bytes(b"\x68\x08\x00\xFF\x12")
            + bytes([channel])
            + bytes([17 + channel])
            + bytes(b"\x16")
        )

# 对比字符串相似
# 可用于对比红外信号预留值
# 因为硬件红外模块即使是接收到相同的红外信号，
# 由于模拟信号转为数字存储时的误差，会导致并不能完全相等（数字值的不同并不影响解调成红外信号发射时的正确性，硬件模块特点如此，认了就好）
def approximate_similarity(s1, s2):
    m = len(s1)
    n = len(s2)

    # 创建一个 (m+1) x (n+1) 的二维数组，用于存储 LCS 的长度
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # 填充 dp 数组
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # 计算两个字符串的近似度
    similarity = dp[m][n] / max(m, n)
    return similarity


def show_on():
    digit_machine_motor.run_to_degrees_counted(0)


def show_off():
    digit_machine_motor.run_to_degrees_counted(685)


def show_init():
    digit_machine_motor.run_to_degrees_counted(0)


def finger_out(length):
    finger_motor.run_for_degrees(length, 100)
    finger_motor.run_for_degrees(0 - length, 100)


def pitch_move(position):
    pitch_motor.run_for_degrees(position, 100)


def turn_on():
    pitch_move(-320)
    finger_out(400)
    pitch_move(320)
    show_on()


def turn_off():
    pitch_move(-400)
    finger_out(590)
    pitch_move(400)
    show_off()


def init_distance_mode():
    light = "OFF"
    while True:
        sleep_ms(100)
        distance.light_up_all(100)
        cm = distance.get_distance_cm()
        if cm != None and cm <= 5:
            distance.light_up_all(1)
            if light == "OFF":
                turn_on()
                light = "ON"
            else:
                turn_off()
                light = "OFF"


def init_ir_mode():
    light = "OFF"
    ir = IR(ir_sensor)
    while True:
        ir.wait_for_receive(0) # 任何红外信号都可触发
        # code = ir.wait_for_receive(0)
        # approximate_similarity(code, IR_TURN_ON_CODE)
        if  light == "OFF":
            turn_on()
            light = "ON"
        else:
            turn_off()
            light = "OFF"


if MODE == "DISTANCE_MODE":
    init_distance_mode()
else:
    init_ir_mode()
