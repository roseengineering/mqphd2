#!/usr/bin/python3

import subprocess, time, socket, argparse, json
import paho.mqtt.client as mqtt


parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("--broker", default="0.0.0.0", help='broker host')
parser.add_argument("--broker-port", default=1883, type=int, help='broker port')
parser.add_argument("--broker-keepalive", default=60, type=int, help='broker keepalive seconds')
parser.add_argument("--topic", default="f/tx", help='broker topic for command')

parser.add_argument("--host", default="localhost", help="phd2 remote host")
parser.add_argument("--port", type=int, default=4400, help="phd2 remote port")
parser.add_argument("--shell", default="xvfb-run -s '-screen 0 800x600x8' phd2", help="phd2 shell command")
parser.add_argument("--norun", action="store_true", help="do not run phd on start")


ident = 0
settle_timeout = 60
settle_time = 10
settle_pixels = 1.5

def cast(buf):
    try:
        if buf.isnumeric(): return int(buf)
        return float(buf)
    except:
        pass


def gen_topic(name=None):
    d = args.topic.split('/')[:-1]
    if name is not None:
        d.append(name)
    return '/'.join(d)


def on_connect(broker, userdata, flags, rc):
    broker.subscribe(gen_topic('#'))


def broker_init():
    broker = mqtt.Client()
    broker.on_connect = on_connect
    broker.on_message = on_message
    broker.connect(args.broker, args.broker_port, args.broker_keepalive)
    broker.loop_start()
    return broker


def settle_object():
    return { 
        "pixels": settle_pixels, 
        "time": settle_time, 
        "timeout": settle_timeout 
    }


def spawn_phd2():
    subprocess.Popen(args.shell, shell=True)
    time.sleep(2)


def on_message(broker, userdata, msg):
    global settle_timeout, settle_time, settle_pixels
    payload = msg.payload.decode('latin').strip()
    if payload and msg.topic == args.topic:
        cmd, _, param = payload.lower().partition(' ') 
        param = param.strip()
        if cmd == "c":
            issue("set_connected", True)
        if cmd == "e":
            param = cast(param) or 10
            issue("set_exposure", param)
        if cmd == "s":
            issue("stop_capture")
        if cmd == "l":    
            issue("loop") # loops, finds star, then starts guiding
        if cmd == "fs":
            issue("find_star")
        if cmd == "p":
            issue("set_paused", True)
        if cmd == "u":
            issue("set_paused", False)
        if cmd == "g":
            settle = settle_object()
            issue("guide", { "settle": settle })
        if cmd == "d":
            param = cast(param) or 10
            settle = settle_object()
            issue("guide", { "amount": param, "settle": settle })
        if cmd == "k":
            issue("shutdown")
        if cmd == "run":
            spawn_phd2()

        # setters
        if cmd == "to":
            settle_timeout = cast(param) or 60
        if cmd == "st":
            settle_time = cast(param) or 10
        if cmd == "sp":
            settle_pixels = cast(param) or 1.5

        # getters
        if cmd == "gc":
            issue("get_connected")
        if cmd == "ge":
            issue("get_exposure")
        if cmd == "gs":
            issue("get_app_state")
        if cmd == "gd":
            issue("get_exposure_durations")
        if cmd == "gp":
            issue("get_paused")
        if cmd == "ga":
            issue("get_calibrated")

        # calibration
        if cmd == "cc":
            issue("clear_calibration")
        if cmd == "fc":
            issue("flip_calibration")


def issue(method, param=None):
    global ident
    ident += 1
    d = { 'method': method, 'id': ident }
    if param is not None: 
        d['params'] = param if type(param) is dict else [ param ]
    buf = json.dumps(d)
    print('>', buf)
    sock.sendall(buf.encode() + b'\n')


def readln(s):
    line = b""
    while True:
        part = s.recv(1)
        if part != b"\n":
            line += part
        else:
            yield line.strip().decode()
            line = b""


def main():
    global sock
    if not args.norun:
        spawn_phd2()
    while True:
        sock = None
        broker = broker_init()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((args.host, args.port))
            for line in readln(sock):
                # print(line)
                d = json.loads(line, strict=False) 
                if 'jsonrpc' in d and 'error' in d:
                    buf = d['error']['message']
                    broker.publish(gen_topic('error'), buf)
                elif 'jsonrpc' in d and 'result' in d:
                    res = d['result']
                    buf = res if type(res) is str else json.dumps(res)
                    broker.publish(gen_topic('result'), buf)
                elif 'Event' in d:
                    evt = d['Event']
                    buf = f"{evt}"
                    try:
                        if evt == "Version":
                            buf += f" {d['PHDVersion']}"
                        if evt == "AppState":
                            buf += f" {d['State']}"
                        if evt == "StartCalibration":
                            buf += f" {d['Mount']}"
                        if evt == "Calibrating":
                            buf = f"{d['State']}"
                            buf = ' '.join(buf.split())
                        if evt == "GuideStep":
                            buf = f"HFD {d['HFD']} d {d['AvgDist']}"
                    except KeyError:
                        pass 
                    broker.publish(gen_topic("event"), buf)
                else:
                    buf = json.dumps(d)
                    broker.publish(gen_topic("unknown"), buf)
        except Exception as e:
            print(e)
            broker.publish(gen_topic("exception"), str(e))
            time.sleep(10)
        broker.loop_stop()
        broker.disconnect()


if __name__ == '__main__':
    args = parser.parse_args()
    main()



