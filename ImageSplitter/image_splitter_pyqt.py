import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QFileDialog, 
                             QVBoxLayout, QHBoxLayout, QMessageBox, QSpinBox)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QSettings
from PIL import Image
from io import BytesIO

class ImageSplitter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Grid Splitter with Preview")
        self.image_path = None
        self.pixmap = None
        self.rows = 4
        self.cols = 4
        self.output_dir = None
        self.settings = QSettings("ImageSplitter", "config")
        self.init_ui()
        self.load_settings()

    def init_ui(self):  
        layout = QVBoxLayout() 

        self.btn_file = QPushButton("Select image")  
        self.btn_file.clicked.connect(self.select_file)  
        self.label_file = QLabel("No file selected") 

        grid_layout = QHBoxLayout()  
        grid_layout.addWidget(QLabel("Rows:"))
        self.spin_rows = QSpinBox()  
        self.spin_rows.setMinimum(1)
        self.spin_rows.setMaximum(20)
        self.spin_rows.setValue(4)  
        self.spin_rows.valueChanged.connect(self.update_grid)
        grid_layout.addWidget(self.spin_rows) 

        grid_layout.addWidget(QLabel("Columns:"))
        self.spin_cols = QSpinBox()  
        self.spin_cols.setMinimum(1)
        self.spin_cols.setMaximum(20)
        self.spin_cols.setValue(4)
        self.spin_cols.valueChanged.connect(self.update_grid)
        grid_layout.addWidget(self.spin_cols) 

        self.btn_folder = QPushButton("Select output folder")  
        self.btn_folder.clicked.connect(self.select_folder)  
        self.label_folder = QLabel("No folder selected") 

        self.btn_split = QPushButton("Split image")  
        self.btn_split.clicked.connect(self.split_image) 

        self.image_label = QLabel()
        self.image_label.setMinimumSize(600, 600)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background: #f0f0f0;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.btn_file)  
        layout.addWidget(self.label_file)  
        layout.addLayout(grid_layout)  
        layout.addWidget(self.image_label)
        layout.addWidget(self.btn_folder)  
        layout.addWidget(self.label_folder)  
        layout.addWidget(self.btn_split) 

        self.setLayout(layout) 

    def load_settings(self):
        """Load saved paths and settings from .ini file"""
        self.image_path = self.settings.value("last_image_path", "")
        self.output_dir = self.settings.value("last_output_dir", "")
        self.rows = int(self.settings.value("rows", 4))
        self.cols = int(self.settings.value("cols", 4))
        
        # Update spin boxes FIRST (triggers update_grid)
        self.spin_rows.setValue(self.rows)
        self.spin_cols.setValue(self.cols)
        
        # Update file labels
        if self.image_path and os.path.exists(self.image_path):
            self.label_file.setText(os.path.basename(self.image_path))
            self.load_image()
        else:
            self.label_file.setText("No file selected")
            
        if self.output_dir and os.path.exists(self.output_dir):
            self.label_folder.setText(self.output_dir)
        else:
            self.label_folder.setText("No folder selected")

    def save_settings(self):
        """Save paths and settings to .ini file"""
        self.settings.setValue("last_image_path", self.image_path or "")
        self.settings.setValue("last_output_dir", self.output_dir or "")
        self.settings.setValue("rows", self.spin_rows.value())
        self.settings.setValue("cols", self.spin_cols.value())

    def closeEvent(self, event):
        """Save settings when closing the app"""
        self.save_settings()
        event.accept()

    def select_file(self):  
        start_dir = os.path.dirname(self.image_path) if self.image_path else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select image", start_dir, 
            "Image files (*.jpg *.jpeg *.png *.bmp *.tiff *.gif)"
        )
        if file_path:  
            self.image_path = file_path  
            self.label_file.setText(os.path.basename(file_path))
            self.load_image()
            self.save_settings()

    def load_image(self):
        try:
            pil_image = Image.open(self.image_path).convert('RGB')
            img_buffer = BytesIO()
            pil_image.save(img_buffer, format='PNG')
            qimage = QImage()
            qimage.loadFromData(img_buffer.getvalue())
            
            self.pixmap = QPixmap.fromImage(qimage).scaled(
                580, 580, Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            # Grid updates automatically via spin_rows/cols valueChanged signals
            self.update_grid()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot load image: {str(e)}")
            self.pixmap = None

    def update_grid(self):
        if self.pixmap is None:
            return
            
        self.rows = self.spin_rows.value()
        self.cols = self.spin_cols.value()
        self.save_settings()  # Save rows/cols changes
        
        grid_pixmap = self.pixmap.copy()
        painter = QPainter(grid_pixmap)
        
        pen = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        w = grid_pixmap.width() / self.cols
        h = grid_pixmap.height() / self.rows
        
        # Vertical lines
        for i in range(1, self.cols):
            x = int(i * w)
            painter.drawLine(x, 0, x, grid_pixmap.height())
        
        # Horizontal lines
        for i in range(1, self.rows):
            y = int(i * h)
            painter.drawLine(0, y, grid_pixmap.width(), y)
        
        painter.end()
        self.image_label.setPixmap(grid_pixmap)

    def select_folder(self):  
        start_dir = self.output_dir if self.output_dir else ""
        folder = QFileDialog.getExistingDirectory(self, "Select output folder", start_dir)  
        if folder:  
            self.output_dir = folder  
            self.label_folder.setText(folder)
            self.save_settings()

    def get_unique_filename(self, output_dir, base_name, extension):
        """Generate unique filename by adding _1, _2, etc. if needed"""
        filepath = os.path.join(output_dir, f"{base_name}{extension}")
        counter = 1
        
        while os.path.exists(filepath):
            filepath = os.path.join(output_dir, f"{base_name}_{counter}{extension}")
            counter += 1
            
        return filepath

    def split_image(self):  
        if not self.image_path or not self.output_dir:  
            QMessageBox.warning(self, "Warning", "Select image and output folder")  
            return  

        try:
            rows = self.spin_rows.value()  
            cols = self.spin_cols.value()  

            img = Image.open(self.image_path)  
            width, height = img.size  
            w = width // cols  
            h = height // rows  

            count = 1  
            saved_count = 0
            
            for i in range(rows):  
                for j in range(cols):  
                    box = (j*w, i*h, (j+1)*w, (i+1)*h)  
                    cell = img.crop(box)  
                    
                    filename = self.get_unique_filename(self.output_dir, f"photo_{count}", ".png")
                    cell.save(filename)  
                    saved_count += 1
                    count += 1  

            QMessageBox.information(self, "Completed", 
                                  f"{saved_count} images saved in {self.output_dir}") 
            self.save_settings()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Save error: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splitter = ImageSplitter()
    splitter.show()
    sys.exit(app.exec())
