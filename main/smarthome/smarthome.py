import struct
import time
import wave

import numpy as np
import soundfile
from pynq import Xlnk
from pynq.lib.arduino import Arduino_IO
from pynq.overlays.base import BaseOverlay

import api
import mfcc

devpid = 1537
base_url = "https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s"
APIKey = "usDNEeyDfcEZEkqvfbprls97"
SecretKey = "65KhWbbm6PRTjGVNR0PR6qg1aDehDriC"
HOST = base_url % (APIKey, SecretKey)
path = "/home/xilinx/mywork/smarthome/record/recording.wav"
login = 0


# 读取bin文件
def readbinfile(filename, size):
    f = open(filename, "rb")
    z = []
    for j in range(size):
        data = f.read(4)
        data_float = struct.unpack("f", data)[0]
        z.append(data_float)
    f.close()
    z = np.array(z)
    return z


# 进入fpga作卷积
def RunConv(conv, Kx, Ky, Sx, Sy, mode, relu_en, feature_in, W, bias, feature_out):
    conv.write(0x10, feature_in.shape[2])
    conv.write(0x18, feature_in.shape[0])
    conv.write(0x20, feature_in.shape[1])
    conv.write(0x28, feature_out.shape[2])
    conv.write(0x30, Kx)
    conv.write(0x38, Ky)
    conv.write(0x40, Sx)
    conv.write(0x48, Sy)
    conv.write(0x50, mode)
    conv.write(0x58, relu_en)
    conv.write(0x60, feature_in.physical_address)
    conv.write(0x68, W.physical_address)
    conv.write(0x70, bias.physical_address)
    conv.write(0x78, feature_out.physical_address)
    conv.write(0, (conv.read(0) & 0x80) | 0x01)
    tp = conv.read(0)
    while not ((tp >> 1) & 0x1):
        tp = conv.read(0)


# 进入fpga做池化
def RunPool(pool, Kx, Ky, mode, feature_in, feature_out):
    pool.write(0x10, feature_in.shape[2])
    pool.write(0x18, feature_in.shape[0])
    pool.write(0x20, feature_in.shape[1])
    pool.write(0x28, Kx)
    pool.write(0x30, Ky)
    pool.write(0x38, mode)
    pool.write(0x40, feature_in.physical_address)
    pool.write(0x48, feature_out.physical_address)
    pool.write(0, (pool.read(0) & 0x80) | 0x01)
    while not ((pool.read(0) >> 1) & 0x1):
        pass


# 命令判断与执行
def order(overlay, order_str):
    global login
    green = Arduino_IO(base.ARDUINO,14,"out")
    yellow = Arduino_IO(base.ARDUINO,15,"out")
    red = Arduino_IO(base.ARDUINO,16,"out")
    
    huang_deng = ["开", "黄", "灯"]
    if all(name in order_str for name in huang_deng):
        pAudio.load("/home/xilinx/mywork/smarthome/record/yled.wav")
        pAudio.play()
       # overlay.rgbleds[4].write(6)
        yellow.write(1)
        
    lv_deng = ["开", "绿", "灯"]
    if all(name in order_str for name in lv_deng):
        pAudio.load("/home/xilinx/mywork/smarthome/record/gled.wav")
        pAudio.play()
        # overlay.rgbleds[4].write(2)
        green.write(1)
        
    hong_deng = ["开", "红", "灯"]
    if all(name in order_str for name in hong_deng):
        pAudio.load("/home/xilinx/mywork/smarthome/record/rled.wav")
        pAudio.play()
        # overlay.rgbleds[4].write(4)
        red.write(1)
    
    g_huang_deng = ["关", "黄", "灯"]
    if all(name in order_str for name in g_huang_deng):
        pAudio.load("/home/xilinx/mywork/smarthome/record/clled.wav")
        pAudio.play()
       # overlay.rgbleds[4].write(6)
        yellow.write(0)
    
    g_lv_deng = ["关", "绿", "灯"]
    if all(name in order_str for name in g_lv_deng):
        pAudio.load("/home/xilinx/mywork/smarthome/record/clled.wav")
        pAudio.play()
        # overlay.rgbleds[4].write(2)
        green.write(0) 
    
    g_hong_deng = ["关", "红", "灯"]
    if all(name in order_str for name in g_hong_deng):
        pAudio.load("/home/xilinx/mywork/smarthome/record/clled.wav")
        pAudio.play()
        # overlay.rgbleds[4].write(4)
        red.write(0)

    guan_deng = ["关","所有", "灯"]
    if all(name in order_str for name in guan_deng):
        pAudio.load("/home/xilinx/mywork/smarthome/record/clled.wav")
        pAudio.play()
        # overlay.rgbleds[4].write(0)
        yellow.write(0)
        green.write(0)
        red.write(0)
    
    deng_lu = "上号"
    if deng_lu in order_str:
        pAudio.load("/home/xilinx/mywork/smarthome/record/sh.wav")
        pAudio.play()
        login = 1
        overlay.rgbleds[5].write(7)
    
    zhu_xiao = "注销"
    if zhu_xiao in order_str:
        pAudio.load("/home/xilinx/mywork/smarthome/record/zx.wav")
        pAudio.play()
        login = 0
        overlay.rgbleds[5].write(0)


# 声纹识别
def cal_label():
    # conv1
    RunConv(conv, KERNEL_WIDTH1, KERNEL_HEIGHT1, X_STRIDE1, Y_STRIDE1, MODE1, RELU_EN1, voice, W_conv1, b_conv1,
            h_conv1)
    RunPool(pool, KERNEL_WIDTH11, KERNEL_HEIGHT11, MODE11, h_conv1, h_pool1)
    # conv2
    RunConv(conv, KERNEL_WIDTH2, KERNEL_HEIGHT2, X_STRIDE2, Y_STRIDE2, MODE2, RELU_EN2, h_pool1, W_conv2, b_conv2,
            h_conv2)
    RunPool(pool, KERNEL_WIDTH21, KERNEL_HEIGHT21, MODE21, h_conv2, h_pool2)
    # fc1
    RunConv(conv, KERNEL_WIDTH3, KERNEL_HEIGHT3, X_STRIDE3, Y_STRIDE3, MODE3, RELU_EN3, h_pool2, W_fc1, b_fc1,
            h_fc1)
    # fc2
    RunConv(conv, KERNEL_WIDTH4, KERNEL_HEIGHT4, X_STRIDE4, Y_STRIDE4, MODE4, RELU_EN4, h_fc1, W_fc2, b_fc2,
            h_fc2)

    print("Hardware run finish")
    MAX = h_fc2[0][0][0]
    label_num = 0
    s = MAX
    for i in range(1, OUT_CH4):
        s += h_fc2[0][0][i]
        if h_fc2[0][0][i] > MAX:
            MAX = h_fc2[0][0][i]
            label_num = i
    accuracy = MAX / s
    return label_num, accuracy


# 声纹验证
def recognize(sound):
    print("Reading voice...")
    rd_time_start = time.time()
    wave_data = np.fromstring(sound, dtype=np.short)
    wave_data.shape = -1, 2
    wave_data = wave_data.T
    feat = mfcc.calcMFCC_delta_delta(wave_data[0][0:50000], framerate)[20:100, :36]
    voice1 = feat - feat.min()
    voice1 = voice1 / voice1.max()
    for i in range(IN_HEIGHT1):
        for j in range(IN_WIDTH1):
            for k in range(IN_CH1):
                voice[i][j][k] = voice1[i][j]
    rd_time_end = time.time()
    print("Finish reading voice, ", "time cost", rd_time_end - rd_time_start, "s", " recognizing...")

    rg_time_start = time.time()
    label_num, accuracy = cal_label()
    rg_time_end = time.time()
    print("The voice number is " + str(label_num) + " with accuracy of " + str(accuracy))
    print("time cost", rg_time_end - rg_time_start, "s")
    return label_num, accuracy


# 格式转换
def trans_wav(sound):
    ts_time_start = time.time()
    print("Transforming wav...")
    buf = b''
    barr = bytearray(buf)
    for i in range(len(sound)):
        if i % 6 == 0:
            barr.append(sound[i])
    p = bytes(barr)
    fout = wave.open("/home/xilinx/mywork/smarthome/record/output.wav", "wb")
    fout.setparams(params)
    fout.setframerate(16000)
    fout.setnchannels(1)
    fout.writeframes(p)
    ts_time_end = time.time()
    print("Success to transform wav, ", "time cost", ts_time_end - ts_time_start, "s")


# 初始化矩阵大小
# Conv1
IN_WIDTH1 = 36
IN_HEIGHT1 = 80
IN_CH1 = 1

KERNEL_WIDTH1 = 3
KERNEL_HEIGHT1 = 3
X_STRIDE1 = 1
Y_STRIDE1 = 1

RELU_EN1 = 1
MODE1 = 1  # 0:VALID, 1:SAME
if MODE1:
    X_PADDING1 = int((KERNEL_WIDTH1 - 1) / 2)
    Y_PADDING1 = int((KERNEL_HEIGHT1 - 1) / 2)
else:
    X_PADDING1 = 0
    Y_PADDING1 = 0

OUT_CH1 = 16
OUT_WIDTH1 = int((IN_WIDTH1 + 2 * X_PADDING1 - KERNEL_WIDTH1) / X_STRIDE1 + 1)
OUT_HEIGHT1 = int((IN_HEIGHT1 + 2 * Y_PADDING1 - KERNEL_HEIGHT1) / Y_STRIDE1 + 1)

# Pool1
MODE11 = 2  # mode: 0:MEAN, 1:MIN, 2:MAX
IN_WIDTH11 = OUT_WIDTH1
IN_HEIGHT11 = OUT_HEIGHT1
IN_CH11 = OUT_CH1

KERNEL_WIDTH11 = 2
KERNEL_HEIGHT11 = 2

OUT_CH11 = IN_CH11
OUT_WIDTH11 = int(IN_WIDTH11 / KERNEL_WIDTH11)
OUT_HEIGHT11 = int(IN_HEIGHT11 / KERNEL_HEIGHT11)

# Conv2
IN_WIDTH2 = OUT_WIDTH11
IN_HEIGHT2 = OUT_HEIGHT11
IN_CH2 = OUT_CH11

KERNEL_WIDTH2 = 3
KERNEL_HEIGHT2 = 3
X_STRIDE2 = 1
Y_STRIDE2 = 1

RELU_EN2 = 1
MODE2 = 1  # 0:VALID, 1:SAME
if MODE2:
    X_PADDING2 = int((KERNEL_WIDTH2 - 1) / 2)
    Y_PADDING2 = int((KERNEL_HEIGHT2 - 1) / 2)
else:
    X_PADDING2 = 0
    Y_PADDING2 = 0

OUT_CH2 = 32
OUT_WIDTH2 = int((IN_WIDTH2 + 2 * X_PADDING2 - KERNEL_WIDTH2) / X_STRIDE2 + 1)
OUT_HEIGHT2 = int((IN_HEIGHT2 + 2 * Y_PADDING2 - KERNEL_HEIGHT2) / Y_STRIDE2 + 1)

# Pool2
MODE21 = 2  # mode: 0:MEAN, 1:MIN, 2:MAX
IN_WIDTH21 = OUT_WIDTH2
IN_HEIGHT21 = OUT_HEIGHT2
IN_CH21 = OUT_CH2

KERNEL_WIDTH21 = 2
KERNEL_HEIGHT21 = 2

OUT_CH21 = IN_CH21
OUT_WIDTH21 = int(IN_WIDTH21 / KERNEL_WIDTH21)
OUT_HEIGHT21 = int(IN_HEIGHT21 / KERNEL_HEIGHT21)

# Fc1
IN_WIDTH3 = OUT_WIDTH21
IN_HEIGHT3 = OUT_HEIGHT21
IN_CH3 = OUT_CH21

KERNEL_WIDTH3 = 9
KERNEL_HEIGHT3 = 20
X_STRIDE3 = 1
Y_STRIDE3 = 1

RELU_EN3 = 1
MODE3 = 0  # 0:VALID, 1:SAME
if MODE3:
    X_PADDING3 = int((KERNEL_WIDTH3 - 1 / 2))
    Y_PADDING3 = int((KERNEL_HEIGHT3 - 1) / 2)
else:
    X_PADDING3 = 0
    Y_PADDING3 = 0

OUT_CH3 = 128
OUT_WIDTH3 = int((IN_WIDTH3 + 2 * X_PADDING3 - KERNEL_WIDTH3) / X_STRIDE3 + 1)
OUT_HEIGHT3 = int((IN_HEIGHT3 + 2 * Y_PADDING3 - KERNEL_HEIGHT3) / Y_STRIDE3 + 1)

# Fc2
IN_WIDTH4 = OUT_WIDTH3
IN_HEIGHT4 = OUT_HEIGHT3
IN_CH4 = OUT_CH3

KERNEL_WIDTH4 = 1
KERNEL_HEIGHT4 = 1
X_STRIDE4 = 1
Y_STRIDE4 = 1

RELU_EN4 = 1
MODE4 = 0  # 0:VALID, 1:SAME
if MODE4:
    X_PADDING4 = int((KERNEL_WIDTH4 - 1 / 2))
    Y_PADDING4 = int((KERNEL_HEIGHT4 - 1) / 2)
else:
    X_PADDING4 = 0
    Y_PADDING4 = 0

OUT_CH4 = 10
OUT_WIDTH4 = int((IN_WIDTH4 + 2 * X_PADDING4 - KERNEL_WIDTH4) / X_STRIDE4 + 1)
OUT_HEIGHT4 = int((IN_HEIGHT4 + 2 * Y_PADDING4 - KERNEL_HEIGHT4) / Y_STRIDE4 + 1)

# 开辟空间
xlnk = Xlnk()

print("Overlay downloading...")
ol_time_start = time.time()
base = BaseOverlay("base.bit")
conv = base.Conv_0
pool = base.Pool_0
ol_time_end = time.time()
print("Overlay download finish, ", "time cost", ol_time_end-ol_time_start, "s")

voice = xlnk.cma_array(shape=(IN_HEIGHT1, IN_WIDTH1, IN_CH1), cacheable=0, dtype=np.float32)

print("Initialing matrix...")
mt_time_start = time.time()
# conv1
W_conv1 = xlnk.cma_array(shape=(KERNEL_HEIGHT1, KERNEL_WIDTH1, IN_CH1, OUT_CH1), cacheable=0, dtype=np.float32)
b_conv1 = xlnk.cma_array(shape=(OUT_CH1), cacheable=0, dtype=np.float32)
h_conv1 = xlnk.cma_array(shape=(OUT_HEIGHT1, OUT_WIDTH1, OUT_CH1), cacheable=0, dtype=np.float32)
h_pool1 = xlnk.cma_array(shape=(OUT_HEIGHT11, OUT_WIDTH11, OUT_CH11), cacheable=0, dtype=np.float32)

# conv2
W_conv2 = xlnk.cma_array(shape=(KERNEL_HEIGHT2, KERNEL_WIDTH2, IN_CH2, OUT_CH2), cacheable=0, dtype=np.float32)
b_conv2 = xlnk.cma_array(shape=(OUT_CH2), cacheable=0, dtype=np.float32)
h_conv2 = xlnk.cma_array(shape=(OUT_HEIGHT2, OUT_WIDTH2, OUT_CH2), cacheable=0, dtype=np.float32)
h_pool2 = xlnk.cma_array(shape=(OUT_HEIGHT21, OUT_WIDTH21, OUT_CH21), cacheable=0, dtype=np.float32)

# fc1
W_fc1 = xlnk.cma_array(shape=(KERNEL_HEIGHT3, KERNEL_WIDTH3, IN_CH3, OUT_CH3), cacheable=0, dtype=np.float32)
b_fc1 = xlnk.cma_array(shape=(OUT_CH3), cacheable=0, dtype=np.float32)
h_fc1 = xlnk.cma_array(shape=(OUT_HEIGHT3, OUT_WIDTH3, OUT_CH3), cacheable=0, dtype=np.float32)

# fc2
W_fc2 = xlnk.cma_array(shape=(KERNEL_HEIGHT4, KERNEL_WIDTH4, IN_CH4, OUT_CH4), cacheable=0, dtype=np.float32)
b_fc2 = xlnk.cma_array(shape=(OUT_CH4), cacheable=0, dtype=np.float32)
h_fc2 = xlnk.cma_array(shape=(OUT_HEIGHT4, OUT_WIDTH4, OUT_CH4), cacheable=0, dtype=np.float32)

# 读取权重，偏置
w_conv1 = readbinfile("/home/xilinx/mywork/smarthome/data/W_conv1.bin", KERNEL_HEIGHT1 * KERNEL_WIDTH1 * IN_CH1 * OUT_CH1)
w_conv1 = w_conv1.reshape((KERNEL_HEIGHT1, KERNEL_WIDTH1, IN_CH1, OUT_CH1))
for i in range(KERNEL_HEIGHT1):
    for j in range(KERNEL_WIDTH1):
        for k in range(IN_CH1):
            for l in range(OUT_CH1):
                W_conv1[i][j][k][l] = w_conv1[i][j][k][l]
B_conv1 = readbinfile("/home/xilinx/mywork/smarthome/data/b_conv1.bin", OUT_CH1)
print("Finish initial w_conv1")

for i in range(OUT_CH1):
    b_conv1[i] = B_conv1[i]
print("Finish initial b_conv1")

w_conv2 = readbinfile("/home/xilinx/mywork/smarthome/data/W_conv2.bin", KERNEL_HEIGHT2 * KERNEL_WIDTH2 * IN_CH2 * OUT_CH2)
w_conv2 = w_conv2.reshape((KERNEL_HEIGHT2, KERNEL_WIDTH2, IN_CH2, OUT_CH2))
for i in range(KERNEL_HEIGHT2):
    for j in range(KERNEL_WIDTH2):
        for k in range(IN_CH2):
            for l in range(OUT_CH2):
                W_conv2[i][j][k][l] = w_conv2[i][j][k][l]
B_conv2 = readbinfile("/home/xilinx/mywork/smarthome/data/b_conv2.bin", OUT_CH2)
print("Finish initial w_conv2")

for i in range(OUT_CH2):
    b_conv2[i] = B_conv2[i]
print("Finish initial b_conv2")

fc_time_start = time.time()
w_fc1 = readbinfile("/home/xilinx/mywork/smarthome/data/W_fc1.bin", KERNEL_HEIGHT3 * KERNEL_WIDTH3 * IN_CH3 * OUT_CH3)
w_fc1 = w_fc1.reshape((KERNEL_HEIGHT3, KERNEL_WIDTH3, IN_CH3, OUT_CH3))
for i in range(KERNEL_HEIGHT3):
    for j in range(KERNEL_WIDTH3):
        for k in range(IN_CH3):
            for l in range(OUT_CH3):
                W_fc1[i][j][k][l] = w_fc1[i][j][k][l]
B_fc1 = readbinfile("/home/xilinx/mywork/smarthome/data/b_fc1.bin", OUT_CH3)
fc_time_end = time.time()
print("Finish initial w_fc1, ", "time cost", fc_time_end-fc_time_start, "s")

for i in range(OUT_CH3):
    b_fc1[i] = B_fc1[i]
print("Finish initial b_fc1")

w_fc2 = readbinfile("/home/xilinx/mywork/smarthome/data/W_fc2.bin", KERNEL_HEIGHT4 * KERNEL_WIDTH4 * IN_CH4 * OUT_CH4)
w_fc2 = w_fc2.reshape((KERNEL_HEIGHT4, KERNEL_WIDTH4, IN_CH4, OUT_CH4))
for i in range(KERNEL_HEIGHT4):
    for j in range(KERNEL_WIDTH4):
        for k in range(IN_CH4):
            for l in range(OUT_CH4):
                W_fc2[i][j][k][l] = w_fc2[i][j][k][l]
B_fc2 = readbinfile("/home/xilinx/mywork/smarthome/data/b_fc2.bin", OUT_CH4)
print("Finish initial w_fc2")

for i in range(OUT_CH4):
    b_fc2[i] = B_fc2[i]
print("Finish initial b_fc2")

pAudio = base.audio
pAudio.select_line_in()
# pAudio.configure(sample_rate=16000)
mt_time_end = time.time()

print("Finish initial, ", "time cost", mt_time_end-mt_time_start, "s")

flag = 1
while base.buttons[3].read() == 0:
    if flag:
        print("Press BUTN0 to record, BUTN3 to exit...")
        flag = 0
    if base.buttons[0].read() == 1:
        flag = 1
        print("Recording voice...")
        pAudio.record(4)
        pAudio.save(path)
        data, samplerate = soundfile.read(path)
        # 24bit转换16bit
        soundfile.write("/home/xilinx/mywork/smarthome/record/recording0.wav", data, samplerate, subtype='PCM_16')
        f = wave.open(r"/home/xilinx/mywork/smarthome/record/recording0.wav", "rb")
        params = f.getparams()
        nchannels, sampwidth, framerate, nframes = params[:4]
        str_data = f.readframes(nframes)

        if login:
            TOKEN = api.getToken(HOST)
            trans_wav(str_data)
            f.close()
            speech = api.get_audio("/home/xilinx/mywork/smarthome/record/output.wav")
            result = api.speech2text(speech, TOKEN, int(devpid))
            print("Your order is： " + str(result))
            order(base, result)

        else:
            label, accu = recognize(str_data)

            if (label == 9) and (accu > 0.6):
                TOKEN = api.getToken(HOST)
                trans_wav(str_data)
                f.close()
                speech = api.get_audio("/home/xilinx/mywork/smarthome/record/output.wav")
                result = api.speech2text(speech, TOKEN, int(devpid))
                print("Your order is： " + str(result))
                order(base, result)
            else:
                pAudio.load("/home/xilinx/mywork/smarthome/record/noauth.wav")
                pAudio.play()

print("exit..")
