import socket
import threading
import pyaudio
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label

class WalkieTalkieApp(App):
    def build(self):
        self.server_socket = None
        self.client_socket = None
        self.audio_stream = None
        self.is_talking = False
        self.chunk_size = 1024  # Small chunks to ensure compatibility
        self.packet_size = 1024  # UDP packet size

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Port setup
        self.port_input = TextInput(hint_text='Enter your port (e.g., 5000)', multiline=False)
        layout.add_widget(self.port_input)
        set_port_btn = Button(text='Set Port', size_hint=(1, 0.2))
        set_port_btn.bind(on_press=self.set_port)
        layout.add_widget(set_port_btn)

        # Connect to target
        self.target_port_input = TextInput(hint_text='Enter target port', multiline=False)
        layout.add_widget(self.target_port_input)
        connect_btn = Button(text='Connect', size_hint=(1, 0.2))
        connect_btn.bind(on_press=self.connect_to_target)
        layout.add_widget(connect_btn)

        # Talk button
        self.talk_btn = Button(text='Talk', size_hint=(1, 0.2), disabled=True)
        self.talk_btn.bind(on_press=self.start_talking)
        self.talk_btn.bind(on_release=self.stop_talking)
        layout.add_widget(self.talk_btn)

        # Status label
        self.status_label = Label(text='Waiting for settings...')
        layout.add_widget(self.status_label)

        return layout

    def set_port(self, instance):
        try:
            port = int(self.port_input.text)
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind(('', port))
            self.status_label.text = f'Port set: {port}'
            threading.Thread(target=self.receive_audio, daemon=True).start()
        except Exception as e:
            self.status_label.text = f'Error setting port: {e}'

    def connect_to_target(self, instance):
        try:
            target_port = int(self.target_port_input.text)
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.target_address = ('127.0.0.1', target_port)  # Localhost for testing
            self.status_label.text = 'Connected to target'
            self.talk_btn.disabled = False
        except Exception as e:
            self.status_label.text = f'Error connecting to target: {e}'

    def start_talking(self, instance):
        if not self.audio_stream:
            self.init_audio_stream()
        self.is_talking = True
        threading.Thread(target=self.send_audio, daemon=True).start()

    def stop_talking(self, instance):
        self.is_talking = False

    def init_audio_stream(self):
        audio = pyaudio.PyAudio()
        self.audio_stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=self.chunk_size)

    def send_audio(self):
        while self.is_talking:
            try:
                data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                # Split data into smaller packets
                for i in range(0, len(data), self.packet_size):
                    packet = data[i:i + self.packet_size]
                    self.client_socket.sendto(packet, self.target_address)
            except Exception as e:
                self.status_label.text = f'Error sending audio: {e}'
                break

    def receive_audio(self):
        audio = pyaudio.PyAudio()
        output_stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True)
        while True:
            try:
                data, addr = self.server_socket.recvfrom(self.packet_size)
                output_stream.write(data)
            except Exception as e:
                print(f'Error receiving audio: {e}')
                continue

if __name__ == '__main__':
    WalkieTalkieApp().run()
