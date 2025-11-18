from PyQt5 import QtWidgets, uic
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice



i = 0
distances = array.array('d',[0,0,0])

app = QtWidgets.QApplication([])
ui = uic.loadUi("CrabControlls.ui")

serial = QSerialPort()
serial.setBaudRate(115200)
portList = []
ports = QSerialPortInfo().availablePorts()
for port in ports:
    portList.append(port.portName())
ui.portComboBox.addItems(portList)

def onConnect():
    serial.setPortName(ui.portComboBox.currentText())
    serial.open(QIODevice.ReadWrite)
    checkConnect()

def onDisconnect():
    serial.close()
    checkConnect()

def checkConnect():
    if (serial.isOpen()):
        ui.checkConBox.setCheckState(1)
    else:
        ui.checkConBox.setCheckState(0)

def distReqest():
    request = ("0,0,0,1,0;");
    serial.write(request.encode())


def readPort():
    readBytes = serial.readLine()
    readBytes = str(readBytes, 'UTF-8').strip()
    data = readBytes.split(',')
    print(data)



ui.conButton.clicked.connect(onConnect)
ui.disconButton.clicked.connect(onDisconnect)

ui.distReqBttn.clicked.connect(distReqest)

ui.checkConBox.clicked.connect(checkConnect)

serial.readyRead.connect(readPort)

ui.show()
app.exec()