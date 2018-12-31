# PyMIDI Keyboard build 0.1a
#
# Tested under Python 3.7 (OS X 10.14 Mojave)
#
# Require pyFluidSynth module: https://github.com/nwhitehead/pyfluidsynth

import sys
import time
import fluidsynth
from threading import Timer
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import Qt
from MIDI_QT1 import Ui_MainWindow


class MyWidget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.fs = fluidsynth.Synth(gain=1.2)
        self.fs.start('coreaudio')

        self.keys = [self.C_3, self.Db3, self.D_3, self.Eb3, self.E_3, self.F_3, self.Gb3,
                     self.G_3, self.Ab3, self.A_3, self.Bb3, self.B_3]

        self.choose_soundbank.pressed.connect(self.style_pressed_btn)
        self.choose_soundbank.released.connect(self.choose_files)
        self.record_btn.pressed.connect(self.style_pressed_btn)
        self.record_btn.released.connect(self.start_rec)
        self.record_btn.rec = False
        self.rec = []
        self.rec_time = 0
        self.play_btn.released.connect(self.play_rec)
        self.play_btn.pressed.connect(self.style_pressed_btn)
        self.playback = False
        self.set_btn_released_style(self.play_btn)
        self.set_btn_released_style(self.choose_soundbank)
        self.set_btn_released_style(self.record_btn)
        self.set_btn_released_style(self.prev_oct)
        self.set_btn_released_style(self.next_oct)

        self.oct_now = self.oct.value() + 1
        self.oct.valueChanged.connect(self.set_octave)
        self.oct.setValue(3)
        self.oct.lineEdit().setReadOnly(True)
        self.prev_oct.released.connect(self.prev_octave)
        self.next_oct.released.connect(self.next_octave)
        self.prev_oct.pressed.connect(self.style_pressed_btn)
        self.next_oct.pressed.connect(self.style_pressed_btn)

        self.gr_piano.path = './SoundFonts/Piano Grand.SF2'
        self.piano_col.path = './SoundFonts/Piano Collection.SF2'
        self.ac_guitar.path = './SoundFonts/AcousticGuitar.SF2'
        self.user_sb.path = None
        self.user_sb.setEnabled(False)
        for rb in self.buttonGroup.buttons():
            rb.released.connect(self.set_soundbank)
        self.buttonGroup.buttons()[0].setChecked(True)
        self.buttonGroup.buttons()[0].released.emit()

        self.C_3.setText('Z')
        self.Db3.setText('S')
        self.D_3.setText('X')
        self.Eb3.setText('D')
        self.E_3.setText('C')
        self.F_3.setText('V')
        self.Gb3.setText('G')
        self.G_3.setText('B')
        self.Ab3.setText('H')
        self.A_3.setText('N')
        self.Bb3.setText('J')
        self.B_3.setText('M')

        for key in self.keys:
            key.setStyleSheet('background-color: white; border-color: black; border-style: solid; border-width: 4px; '
                              'padding-bottom: -150px; font-size: 25px')

            key.pressed.connect(self.key_pressed)
            key.released.connect(self.key_released)

            key.setAutoRepeat(True)
            key.setAutoRepeatDelay(10 ** 10)
            key.setAutoRepeatInterval(10 ** 10)
            key._state = 0

            key.proc = None
            key.sharp = False

        i = 1
        while i < len(self.keys):
            self.keys[i].setStyleSheet('background-color: #545556; border-color: black; border-style: solid;'
                                       'border-width: 4px; padding-bottom: -75px; font-size: 25px; color: white')
            self.keys[i].sharp = True
            if i == 3:
                i += 1
            i += 2

    def choose_files(self):
        self.set_btn_released_style(self.sender())
        sf2_file = QFileDialog.getOpenFileName(self, 'Open file',
                                               '/Users/nikitaratasnuk/Desktop/Projects/Yandex/PyQt_Project',
                                               'Sound Fonts Files (*.sf2), (*.SF2)')
        if sf2_file[0] == '':
            return
        # print(sf2_file)
        self.buttonGroup.buttons()[-1].setText(''.join(sf2_file[0].split('/')[-1])[:-4])
        self.buttonGroup.buttons()[-1].adjustSize()

        self.buttonGroup.buttons()[-1].path = sf2_file[0]
        self.buttonGroup.buttons()[-1].setChecked(True)
        self.buttonGroup.buttons()[-1].setEnabled(True)
        self.buttonGroup.buttons()[-1].released.emit()

    def set_soundbank(self):
        self.sfid = self.fs.sfload(self.sender().path)

    def set_octave(self):
        self.oct_now = self.sender().value() + 1

    def prev_octave(self):
        if self.oct.value() > -1:
            self.set_btn_released_style(self.prev_oct)
            self.oct.setValue(self.oct.value() - 1)

    def next_octave(self):
        if self.oct.value() < 8:
            self.set_btn_released_style(self.next_oct)
            self.oct.setValue(self.oct.value() + 1)

    def start_rec(self):
        if self.record_btn.rec:
            for rb in self.buttonGroup.buttons():
                rb.setEnabled(True)
            self.choose_soundbank.setEnabled(True)
            self.play_btn.setEnabled(True)
            self.record_btn.setStyleSheet('background-color: white; border-color: black; border-style: solid;'
                                          'border-width: 4px')
            print(self.rec)
        else:
            self.record_btn.setStyleSheet('background-color: red; border-color: black; border-style: solid;'
                                          'border-width: 4px')
            self.rec = []
            for rb in self.buttonGroup.buttons():
                rb.setEnabled(False)
            self.choose_soundbank.setEnabled(False)
            self.play_btn.setEnabled(False)
            self.rec_sb = [rb for rb in self.buttonGroup.buttons() if rb.isChecked()][0]
        self.record_btn.rec = not self.record_btn.rec

    def timer_repeat(self):
        self.rt.cancel()
        try:
            if self.rec[self.cur_pos][2]:
                self.oct.setValue(self.rec[self.cur_pos][3] - 1)
                self.keys[self.rec[self.cur_pos][1] % 12].pressed.emit()
            else:
                self.oct.setValue(self.rec[self.cur_pos][3] - 1)
                self.keys[self.rec[self.cur_pos][1] % 12].released.emit()
            delta = self.rec[self.cur_pos + 1][0] - self.rec[self.cur_pos][0]
            self.cur_pos += 1
            self.rt = Timer(delta, self.timer_repeat)
            self.rt.start()
        except IndexError:
            self.rt.cancel()
            self.playback = False
            self.play_btn.setText('Start playback')
            self.change_mode_btns()

    def play_rec(self):
        if not self.playback:
            self.playback = True
            self.cur_pos = 0
            self.rt = Timer(0.5, self.timer_repeat)
            self.rt.start()
            self.set_btn_released_style(self.sender())
            self.sender().setText('Stop playback')
        else:
            self.playback = False
            for i in range(len(self.keys)):
                self.keys[i].released.emit()
            self.rt.cancel()
            self.set_btn_released_style(self.sender())
            self.sender().setText('Start playback')
        self.change_mode_btns()

    def change_mode_btns(self):
        for rb in self.buttonGroup.buttons():
            rb.setEnabled(not self.playback)
        self.choose_soundbank.setEnabled(not self.playback)
        self.record_btn.setEnabled(not self.playback)
        self.next_oct.setEnabled(not self.playback)
        self.prev_oct.setEnabled(not self.playback)
        self.oct.setEnabled(not self.playback)

    def style_pressed_btn(self):
        self.set_btn_pressed_style(self.sender())

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Z:
            self.keys[0].pressed.emit()

        if e.key() == Qt.Key_S:
            self.keys[1].pressed.emit()

        if e.key() == Qt.Key_X:
            self.keys[2].pressed.emit()

        if e.key() == Qt.Key_D:
            self.keys[3].pressed.emit()

        if e.key() == Qt.Key_C:
            self.keys[4].pressed.emit()

        if e.key() == Qt.Key_V:
            self.keys[5].pressed.emit()

        if e.key() == Qt.Key_G:
            self.keys[6].pressed.emit()

        if e.key() == Qt.Key_B:
            self.keys[7].pressed.emit()

        if e.key() == Qt.Key_H:
            self.keys[8].pressed.emit()

        if e.key() == Qt.Key_N:
            self.keys[9].pressed.emit()

        if e.key() == Qt.Key_J:
            self.keys[10].pressed.emit()

        if e.key() == Qt.Key_M:
            self.keys[11].pressed.emit()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Z:
            self.keys[0].released.emit()

        if e.key() == Qt.Key_S:
            self.keys[1].released.emit()

        if e.key() == Qt.Key_X:
            self.keys[2].released.emit()

        if e.key() == Qt.Key_D:
            self.keys[3].released.emit()

        if e.key() == Qt.Key_C:
            self.keys[4].released.emit()

        if e.key() == Qt.Key_V:
            self.keys[5].released.emit()

        if e.key() == Qt.Key_G:
            self.keys[6].released.emit()

        if e.key() == Qt.Key_B:
            self.keys[7].released.emit()

        if e.key() == Qt.Key_H:
            self.keys[8].released.emit()

        if e.key() == Qt.Key_N:
            self.keys[9].released.emit()

        if e.key() == Qt.Key_J:
            self.keys[10].released.emit()

        if e.key() == Qt.Key_M:
            self.keys[11].released.emit()

        if e.key() == Qt.Key_Right:
            self.next_octave()

        if e.key() == Qt.Key_Left:
            self.prev_octave()

    def key_pressed(self):
        self.fs.program_select(0, self.sfid, 0, 0)
        if self.record_btn.rec:
            self.rec.append([time.time() - self.rec_time, self.oct_now * 12 + self.keys.index(self.sender()),
                             True, self.oct_now])
        if self.sender()._state == 0:
            self.fs.noteon(0, self.oct_now * 12 + self.keys.index(self.sender()), 90)
        self.sender()._state += 1
        self.set_pressed_style(self.keys.index(self.sender()))

    def key_released(self):
        if not self.sender().isDown():
            if self.record_btn.rec:
                self.rec.append(
                    [time.time() - self.rec_time, self.oct_now * 12 + self.keys.index(self.sender()),
                     False, self.oct_now])
            self.fs.noteoff(0, self.oct_now * 12 + self.keys.index(self.sender()))
            self.sender()._state = 0
            self.set_released_style(self.keys.index(self.sender()))

    def set_pressed_style(self, ind):
        if self.keys[ind].sharp:
            self.keys[ind].setStyleSheet('background-color: #3a3a3a; border-color: black; border-style: solid;'
                                         'border-width: 4px; padding-bottom: -75px; font-size: 25px; color: white')
        else:
            self.keys[ind].setStyleSheet('background-color: lightgrey; border-color: black; border-style: solid;'
                                         'border-width: 4px; padding-bottom: -150px; font-size: 25px')

    def set_released_style(self, ind):
        if self.keys[ind].sharp:
            self.keys[ind].setStyleSheet('background-color: #545556; border-color: black; border-style: solid;'
                                         'border-width: 4px; padding-bottom: -75px; font-size: 25px; color: white')
        else:
            self.keys[ind].setStyleSheet('background-color: white; border-color: black; border-style: solid;'
                                         'border-width: 4px; padding-bottom: -150px; font-size: 25px')

    def set_btn_pressed_style(self, button):
        button.setStyleSheet('background-color: lightgrey; border-color: black; border-style: solid;'
                             'border-width: 4px')

    def set_btn_released_style(self, button):
        button.setStyleSheet('background-color: white; border-color: black; border-style: solid;'
                             'border-width: 4px')

    def print_error(self, text: str):
        self.error_lbl.setStyleSheet('color: #ff0000')
        self.error_lbl.setText('Error: ' + text)
        self.error_lbl.adjustSize()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
