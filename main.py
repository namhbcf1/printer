from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os
import json
import zipfile
from datetime import datetime
from database import Database
from plyer import filechooser

KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: '10dp'
    spacing: '10dp'
    
    MDLabel:
        text: "Phần Mềm Quay Chụp Video Gửi Hàng Trường Phát"
        halign: "center"
        font_style: "H5"
        bold: True
        theme_text_color: "Primary"
        size_hint_y: None
        height: "50dp"
    
    Image:
        id: camera_feed
        allow_stretch: True
        size_hint_y: 0.6
    
    MDLabel:
        id: location_label
        text: "Địa điểm: Đang cập nhật..."
        halign: "center"
        size_hint_y: None
        height: "30dp"
    
    MDLabel:
        id: datetime_label
        text: "Thời gian: "
        halign: "center"
        size_hint_y: None
        height: "30dp"
    
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: "60dp"
        spacing: '10dp'
        padding: '10dp'
        
        MDRaisedButton:
            text: "Bắt đầu quét"
            size_hint_x: 0.3
            on_press: app.start_scanning()
            md_bg_color: (0, 0.5, 1, 1)
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1)
        
        MDRaisedButton:
            text: "Dừng & Lưu"
            size_hint_x: 0.3
            on_press: app.confirm_stop()
            md_bg_color: (1, 0, 0, 1)
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1)
        
        MDRaisedButton:
            text: "Danh sách đơn hàng"
            size_hint_x: 0.3
            on_press: app.show_order_list()
            md_bg_color: (0, 1, 0, 1)
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1)
        
        MDRaisedButton:
            text: "Thoát"
            size_hint_x: 0.3
            on_press: app.stop_app()
            md_bg_color: (0.2, 0.2, 0.2, 1)
            theme_text_color: "Custom"
            text_color: (1, 1, 1, 1)
'''

class CameraApp(MDApp):
    def build(self):
        self.capture = None
        self.scanning = False
        return Builder.load_string(KV)

    def start_scanning(self):
        if self.capture is None:
            self.capture = cv2.VideoCapture(0)
            Clock.schedule_interval(self.update, 1.0 / 30.0)

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.flip(frame, 0)
            barcodes = decode(frame)
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8')
                print(f"Mã quét được: {barcode_data}")
                self.scanning = False
                self.capture.release()
                self.capture = None
                self.process_tracking_number(barcode_data)
                return
            
            buf1 = cv2.flip(frame, 0).tostring()
            image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf1, colorfmt='bgr', bufferfmt='ubyte')
            self.root.ids.camera_feed.texture = image_texture

    def process_tracking_number(self, tracking_number):
        save_dir = os.path.expanduser("~/Videos")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        video_path = os.path.join(save_dir, f"{tracking_number}.mp4")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        location = "Chưa có thông tin địa điểm"
        
        order_info = {
            "tracking_number": tracking_number,
            "video_path": video_path,
            "timestamp": timestamp,
            "location": location
        }
        
        json_data = json.dumps(order_info, indent=4)
        json_path = os.path.join(save_dir, f"{tracking_number}.json")
        with open(json_path, "w") as json_file:
            json_file.write(json_data)
        
        zip_path = os.path.join(save_dir, f"{tracking_number}.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(json_path, os.path.basename(json_path))
            zipf.write(video_path, os.path.basename(video_path))
        
        os.remove(json_path)
        print(f"Video và thông tin đã được lưu vào: {zip_path}")

    def confirm_stop(self):
        self.dialog = MDDialog(
            title="Xác nhận",
            text="Bạn có muốn tiếp tục quay sản phẩm khác hay dừng lại?",
            buttons=[
                MDRaisedButton(text="Tiếp tục", on_press=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="Dừng", on_press=lambda x: self.stop_recording())
            ]
        )
        self.dialog.open()

    def stop_recording(self):
        print("Dừng quay và lưu file...")
        self.scanning = False
        if self.capture:
            self.capture.release()
            self.capture = None
        if self.dialog:
            self.dialog.dismiss()

    def show_order_list(self):
        filechooser.open_file(title="Danh sách đơn hàng", path=os.path.expanduser("~/Videos"))

    def stop_app(self):
        if self.capture:
            self.capture.release()
        self.stop()

if __name__ == "__main__":
    CameraApp().run()
