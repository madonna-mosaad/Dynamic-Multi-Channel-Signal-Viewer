import os
import warnings
import requests
import pyedflib
import weakref
import numpy as np
import pyqtgraph as pg
import tempfile
import shutil
import datetime

from scipy.interpolate import interp1d

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QRect, QSize, Qt, QCoreApplication, QMetaObject, QTimer
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtWidgets import (
    QDialog, QLabel, QPushButton, QColorDialog, QSlider, QComboBox,
    QFileDialog, QVBoxLayout, QMainWindow, QWidget, QHBoxLayout, QLineEdit, QFormLayout
)

from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

warnings.filterwarnings("ignore", category=DeprecationWarning)


class ReplaceSignalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Disable maximize button
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowTitleHint)

        # Set background color and border
        self.setStyleSheet("""
            background-color: rgb(184, 184,184);  /* Background color */
            border: 1px solid rgb(36,36,36);  /* Border size and color */
            color:white;
        """)

        font = QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(17)

        # Label for instruction
        self.label = QLabel(self)
        self.label.setObjectName("label")
        self.label.setGeometry(QRect(10, 30, 261, 91))
        label_font = QFont()
        label_font.setFamily("Times New Roman")
        label_font.setPointSize(24)
        self.label.setFont(label_font)

        # Graph 1 button
        self.load_file_button = QPushButton(self)
        self.load_file_button.setObjectName("load_file_button")
        self.load_file_button.setGeometry(QRect(65, 150, 150, 40))
        self.load_file_button.setMaximumSize(QSize(150, 40))
        self.load_file_button.setFont(font)
        self.load_file_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.load_file_button.setStyleSheet(
            "QPushButton { border: none; padding: 10px; background-color: rgb(36,36,36); "
            "border-bottom: 2px solid transparent; } "
            "QPushButton:hover { background-color: rgb(23, 23, 23); }"
        )

        # Graph 2 button
        self.color_ok_button = QPushButton(self)
        self.color_ok_button.setObjectName("color_ok_button")
        self.color_ok_button.setGeometry(QRect(65, 200, 150, 40))
        self.color_ok_button.setMaximumSize(QSize(150, 40))
        self.color_ok_button.setFont(font)
        self.color_ok_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.color_ok_button.setStyleSheet(
            "QPushButton { border: none; padding: 10px; background-color: rgb(36,36,36); "
            "border-bottom: 2px solid transparent; } "
            "QPushButton:hover { background-color: rgb(23, 23, 23); }"
        )

        # Cancel button
        self.color_cancel_button = QPushButton(self)
        self.color_cancel_button.setObjectName("color_cancel_button")
        self.color_cancel_button.setGeometry(QRect(65, 250, 150, 40))
        self.color_cancel_button.setMaximumSize(QSize(150, 40))
        self.color_cancel_button.setFont(font)
        self.color_cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.color_cancel_button.setStyleSheet(
            "QPushButton { border: none; padding: 10px; background-color: rgb(36,36,36); "
            "border-bottom: 2px solid transparent; } "
            "QPushButton:hover { background-color: rgb(23, 23, 23); }"
        )

        # Set text for label and buttons
        self.retranslateUi()

        # Connect buttons to dialog actions
        self.load_file_button.clicked.connect(self.accept_signal_1)
        self.color_ok_button.clicked.connect(self.accept_signal_2)
        self.color_cancel_button.clicked.connect(self.reject)

        self.selected_signal = None

    def retranslateUi(self):
        self.setWindowTitle("Choose Graph to Replace")
        self.load_file_button.setText("Graph 1")
        self.color_ok_button.setText("Graph 2")
        self.color_cancel_button.setText("Cancel")
        self.label.setText("Choose Graph to Replace")

    def accept_signal_1(self):
        self.selected_signal = 1
        self.accept()

    def accept_signal_2(self):
        self.selected_signal = 2
        self.accept()


class ColorPickerDialog(QDialog):
    def __init__(self, main_window=None):  # Add the main_window argument
        super().__init__()

        self.main_window = main_window  # Store the reference to the main window
        self.selected_color = None
        self.setupUi(self)

        # Connect buttons to color pickers
        self.load_file_button.clicked.connect(self.open_plot_color_picker)
        self.color_graph_button.clicked.connect(self.open_graph_color_picker)
        self.color_fig_button.clicked.connect(self.open_fig_color_picker)
        self.color_labels_button.clicked.connect(self.open_label_color_picker)

        # Connect the Ok and Cancel buttons
        self.color_ok_button.clicked.connect(self.apply_color_changes)  # Ok button
        self.color_cancel_button.clicked.connect(self.reject)  # Cancel button

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(477, 263)
        Dialog.setStyleSheet("background-color: rgb(184, 184,184);")

        font1 = QFont()
        font1.setFamily("Times New Roman")
        font1.setPointSize(17)

        # Label
        self.label = QLabel(Dialog)
        self.label.setObjectName("label")
        self.label.setGeometry(QRect(10, 10, 261, 51))
        font = QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(25)
        self.label.setFont(font)
        self.label.setStyleSheet("color:white")

        # Buttons
        self.color_ok_button = QPushButton(Dialog)
        self.color_ok_button.setGeometry(QRect(350, 200, 100, 40))
        self.color_ok_button.setMaximumSize(QSize(150, 40))
        self.color_ok_button.setFont(font1)
        self.color_ok_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.color_ok_button.setStyleSheet("background-color:rgb(30,30,30); color:white")

        self.load_file_button = QPushButton(Dialog)
        self.load_file_button.setGeometry(QRect(370, 100, 100, 40))
        self.load_file_button.setMaximumSize(QSize(150, 40))
        self.load_file_button.setFont(font1)
        self.load_file_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.load_file_button.setStyleSheet("color:white")

        self.color_cancel_button = QPushButton(Dialog)
        self.color_cancel_button.setGeometry(QRect(230, 200, 100, 40))
        self.color_cancel_button.setMaximumSize(QSize(150, 40))
        self.color_cancel_button.setFont(font1)
        self.color_cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.color_cancel_button.setStyleSheet("background-color:rgb(30,30,30); color:white")

        self.color_graph_button = QPushButton(Dialog)
        self.color_graph_button.setGeometry(QRect(130, 100, 100, 40))
        self.color_graph_button.setMaximumSize(QSize(150, 40))
        self.color_graph_button.setFont(font1)
        self.color_graph_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.color_graph_button.setStyleSheet("color:white")

        self.color_fig_button = QPushButton(Dialog)
        self.color_fig_button.setGeometry(QRect(10, 100, 100, 40))
        self.color_fig_button.setMaximumSize(QSize(150, 40))
        self.color_fig_button.setFont(font1)
        self.color_fig_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.color_fig_button.setStyleSheet("color:white")

        self.color_labels_button = QPushButton(Dialog)
        self.color_labels_button.setGeometry(QRect(250, 100, 100, 40))
        self.color_labels_button.setMaximumSize(QSize(150, 40))
        self.color_labels_button.setFont(font1)
        self.color_labels_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.color_labels_button.setStyleSheet("color:white")

        self.retranslateUi(Dialog)
        QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", "Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", "Select what to Change", None))
        self.color_ok_button.setText(QCoreApplication.translate("Dialog", "Ok", None))
        self.load_file_button.setText(QCoreApplication.translate("Dialog", "Plot", None))
        self.color_cancel_button.setText(QCoreApplication.translate("Dialog", "Cancel", None))
        self.color_graph_button.setText(QCoreApplication.translate("Dialog", "Graph", None))
        self.color_fig_button.setText(QCoreApplication.translate("Dialog", "Figure", None))
        self.color_labels_button.setText(QCoreApplication.translate("Dialog", "Labels", None))

    def open_color_dialog(self, initial_color):
        color = QColorDialog.getColor()  # Opens the color picker dialog
        if color.isValid():
            # Get the RGB values and convert them to 0-1 scale by dividing by 255
            rgb_color = color.getRgb()[:3]  # Get the RGB tuple
            return tuple(c / 255 for c in rgb_color)  # Convert each to a 0-1 range
        return initial_color

    def open_plot_color_picker(self):
        self.selected_color = 'plot'
        self.plot_color = self.open_color_dialog(self.main_window.plot_color)

    def open_graph_color_picker(self):
        self.selected_color = 'graph'
        # Accessing the instance variable with self.main_window
        self.graph_color = self.open_color_dialog(self.main_window.graph_color)  # Use self.main_window

    def open_fig_color_picker(self):
        self.selected_color = 'fig'
        # Accessing the instance variable with self
        self.fig_color = self.open_color_dialog(self.main_window.fig_color)  # Use self.main_window

    def open_label_color_picker(self):
        self.selected_color = 'label'
        # Accessing the instance variable with self
        self.label_color = self.open_color_dialog(self.main_window.label_color)  # Use self.main_window

    def apply_color_changes(self):
        """Apply the selected color based on which color picker was opened."""
        try:
            if self.selected_color == 'plot':
                self.main_window.plot_color = self.plot_color
                print(f"Plot color changed to: {self.main_window.plot_color}")
                self.update_plot_colors()  # Call to update the plot colors

            elif self.selected_color == 'graph':
                self.main_window.graph_color = self.graph_color
                print(f"Graph color changed to: {self.main_window.graph_color}")
                self.update_graph_colors()  # Call to update the graph colors

            elif self.selected_color == 'fig':
                self.main_window.fig_color = self.fig_color
                print(f"Figure color changed to: {self.main_window.fig_color}")
                self.update_canvas_colors()  # Call to update the canvas background color

            elif self.selected_color == 'label':
                self.main_window.label_color = self.label_color
                print(f"Label color changed to: {self.main_window.label_color}")
                self.update_label_colors()  # Call to update the label colors

        except Exception as e:
            print(f"Error applying color changes: {e}")

        self.accept()  # Close the dialog when Ok is pressed

    def update_canvas_colors(self):
        """Updates the figure background color."""
        self.main_window.figure.set_facecolor(self.main_window.fig_color)  # Use main_window for figure
        print(f"Figure background color updated to: {self.main_window.fig_color}")
        self.main_window.canvas.draw_idle()  # Redraw the canvas with updated colors

    def update_plot_colors(self):
        """Updates the plot color."""
        if hasattr(self.main_window, 'line_plot_1'):  # Check line_plot_1 in main_window
            self.main_window.line_plot_1.set_color(self.main_window.plot_color)
            print(f"Plot color updated to: {self.main_window.plot_color}")
        else:
            print("Line plot not found! Cannot update plot color.")
        self.main_window.canvas.draw_idle()  # Redraw the canvas with updated colors

    def update_graph_colors(self):
        """Updates the axes background and tick label colors."""
        if hasattr(self.main_window, 'ax1'):  # Check ax1 in main_window
            self.main_window.ax1.set_facecolor(self.main_window.graph_color)
            self.main_window.ax1.tick_params(colors=self.main_window.label_color)  # Update tick label color
            print(
                f"Graph background and tick labels updated for ax1: {self.main_window.graph_color}, {self.main_window.label_color}")
        else:
            print("ax1 not found! Cannot update graph background for ax1.")

        if hasattr(self.main_window, 'ax2'):  # Check ax2 in main_window
            self.main_window.ax2.set_facecolor(self.main_window.graph_color)
            self.main_window.ax2.tick_params(colors=self.main_window.label_color)  # Update tick label color
            print(
                f"Graph background and tick labels updated for ax2: {self.main_window.graph_color}, {self.main_window.label_color}")
        else:
            print("ax2 not found! Cannot update graph background for ax2.")

        self.main_window.canvas.draw_idle()  # Redraw the canvas with updated colors

    def update_label_colors(self):
        self.main_window.label_color = self.label_color
        print(f"Label color changed to: {self.main_window.label_color}")
        if hasattr(self.main_window, 'ax_polar'):
            self.main_window.ax_polar.tick_params(colors=self.label_color)
            print("Label colors updated.")
        else:
            print("Polar plot not found! Cannot update label colors.")

        self.main_window.canvas.draw_idle()  # Redraw the canvas with updated colors


class GlueSignalsWindow(QMainWindow):
    def __init__(self, signal1, signal2, parent=None):  # Allow a generic parent
        """
        Initialize the GlueSignalsWindow for selecting and gluing signal portions.
        Args:
            signal1: The first signal as a numpy array.
            signal2: The second signal as a numpy array.
            parent: The parent window (typically an instance of QMainWindow or None).
        """
        super().__init__(parent)  # Initialize with the parent if provided
        self.parent_window = weakref.ref(parent) if parent else None  # Store a weak reference to the parent

        # Set window properties for a pop-up
        self.setWindowTitle("Glue Signal Portions")
        self.resize(1280, 700)  # Adjust size to accommodate the new glued signal plot
        self.setWindowModality(QtCore.Qt.ApplicationModal)  # Block interaction with parent until closed
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowTitleHint)

        # Center the window
        screen_geometry = QtWidgets.QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2 + 50
        self.move(x, y)

        # Convert signals to numpy arrays (if not already)
        self.signal1 = np.array(signal1)
        self.signal2 = np.array(signal2)
        self.glued_signal = None  # Initialize a placeholder for the glued signal

        # Set up the user interface
        self.setup_ui()

        # Debug message for initialization
        print("GlueSignalsWindow initialized.")

    def perform_glue(self):
        """
        Perform the glue operation based on selected regions and user input.
        """
        try:
            # Ensure regions are defined
            if not hasattr(self, 'region1') or not hasattr(self, 'region2'):
                raise ValueError("Regions for the signals are not properly defined.")

            # Get selected regions from both signals
            start1, end1 = map(int, self.region1.getRegion())
            start2, end2 = map(int, self.region2.getRegion())

            # Extract portions of the signals
            signal1_portion = self.signal1[start1:end1]
            signal2_portion = self.signal2[start2:end2]

            # Get gap and interpolation order from user input
            gap = self.gap_slider.value()  # Using QSlider for gap
            self.gap_slider_value.setText(f"Gap: {gap}")
            interpolation_order = int(self.interpolation_combo.currentText())  # Using QComboBox for interpolation order

            # Generate the gap signal with interpolation
            gap_signal = self.interpolate_gap(
                np.linspace(signal1_portion[-1], signal2_portion[0], gap + 2),
                interpolation_order
            )

            # Glue the signals
            glued_signal = np.concatenate([signal1_portion, gap_signal, signal2_portion])
            self.glued_signal = glued_signal  # Store the glued signal

            # Generate x-axis ranges for each segment
            x_signal1 = np.arange(len(signal1_portion))
            x_gap = np.arange(len(signal1_portion), len(signal1_portion) + len(gap_signal))
            x_signal2 = np.arange(len(signal1_portion) + len(gap_signal),
                                  len(signal1_portion) + len(gap_signal) + len(signal2_portion))

            # Clear the glued signal plot widget
            self.glued_plot_widget.clear()

            # Plot Signal 1 in blue
            self.glued_plot_widget.plot(x_signal1, signal1_portion, pen=pg.mkPen(color="b", width=2))

            # Plot gap in white
            self.glued_plot_widget.plot(x_gap, gap_signal, pen=pg.mkPen(color="w", width=2))

            # Plot Signal 2 in green
            self.glued_plot_widget.plot(x_signal2, signal2_portion, pen=pg.mkPen(color="g", width=2))

            print("Glued signal plotted with distinct colors.")

        except Exception as e:
            self.show_error_message(f"Error during glue operation: {e}")

    def interpolate_gap(self, gap_signal, order):
        """
        Smooth the gap using robust interpolation.
        Args:
            gap_signal: The signal data for the gap.
            order: The interpolation order (1 for linear, 2 for quadratic, 3 for cubic).
        Returns:
            The interpolated gap signal.
        """
        try:
            # Ensure gap_signal is valid
            gap_signal = np.array(gap_signal)
            if len(gap_signal) < 2:
                print("Insufficient data for interpolation. Returning original gap signal.")
                return gap_signal

            # Create x values for the gap
            x = np.linspace(0, len(gap_signal) - 1, len(gap_signal))

            # Define interpolation kinds
            interpolation_kinds = {1: 'linear', 2: 'quadratic', 3: 'cubic'}
            kind = interpolation_kinds.get(order, 'linear')

            # Ensure sufficient points for quadratic or cubic interpolation
            if kind == 'quadratic' and len(x) < 3:
                print("Insufficient points for quadratic interpolation. Falling back to linear.")
                kind = 'linear'
            elif kind == 'cubic' and len(x) < 4:
                print("Insufficient points for cubic interpolation. Falling back to linear.")
                kind = 'linear'

            # Perform interpolation
            interpolator = interp1d(x, gap_signal, kind=kind, fill_value="extrapolate")
            interpolated_signal = interpolator(np.arange(len(gap_signal)))

            # Check for NaN values in interpolated result
            if np.isnan(interpolated_signal).any():
                print("NaN values detected in interpolated signal. Returning original gap signal.")
                return gap_signal

            return interpolated_signal

        except Exception as e:
            print(f"Error during interpolation: {e}. Returning original gap signal.")
            return gap_signal

    def save_data(self):
        """
        Save snapshots and statistics of signals to arrays, avoiding duplicates for Signal 1 and Signal 2,
        but allowing multiple glued signals if they are different.
        """
        try:
            # Prepare current signal data for saving
            current_snapshot = {
                'Signal 1': self.capture_snapshot(self.signal1, "blue"),
                'Signal 2': self.capture_snapshot(self.signal2, "green")
            }
            current_stats = {
                'Signal 1': self.calculate_statistics(self.signal1),
                'Signal 2': self.calculate_statistics(self.signal2)
            }

            # Check if the current signals (Signal 1 and Signal 2) have already been saved
            def is_duplicate():
                for prev in global_saved_snapshots:
                    if (np.array_equal(prev['Signal 1'], self.signal1) and
                            np.array_equal(prev['Signal 2'], self.signal2)):
                        return True
                return False

            if not is_duplicate():
                # If not duplicates, proceed to handle and save glued signals
                if self.glued_signal is not None:
                    if isinstance(self.glued_signal, list):
                        for index, glued in enumerate(self.glued_signal):
                            key = f'Glued Signal {index + 1}'
                            current_snapshot[key] = self.capture_snapshot(glued, f"red{index + 1}")
                            current_stats[key] = self.calculate_statistics(glued)
                    else:
                        # Single glued signal scenario
                        current_snapshot['Glued Signal'] = self.capture_snapshot(self.glued_signal, "red")
                        current_stats['Glued Signal'] = self.calculate_statistics(self.glued_signal)

                # Append the snapshot and statistics data to the global arrays
                global_saved_snapshots.append(current_snapshot)
                global_saved_statistics.append(current_stats)
                print("Data saved successfully.")
            else:
                # Notify if duplicates are found and not saved
                print("Duplicate Signal 1 and Signal 2 found, not saving.")
        except Exception as e:
            print(f"Error saving data: {e}")

    def capture_snapshot(self, signal, color):
        """
        Capture a snapshot of a signal with unique naming to prevent overwrites.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"signal_{color}_{timestamp}_snapshot.png"
        snapshot_path = os.path.join(tempfile.gettempdir(), filename)
        plt.figure()
        plt.plot(signal, color=color)
        plt.title(f"Signal {color.title()}")
        plt.savefig(snapshot_path)
        plt.close()
        return snapshot_path

    def generate_report(self):
        """
        Generate a professional report with snapshots and statistics for all saved Signal 1, Signal 2,
        and any glued signals. Uses either from live data or from previously saved data arrays.
        """
        try:
            report_path = os.path.join(tempfile.gettempdir(), "Signal_Statistics_Report_Professional.pdf")
            c = canvas.Canvas(report_path, pagesize=letter)
            width, height = letter
            margin = 0.7 * inch
            content_width = width - 2 * margin
            line_spacing = 0.2 * inch

            # Set up the document title and subtitle
            c.setFont("Times-Bold", 20)
            c.drawCentredString(width / 2, height - 1 * inch, "Signal Statistics Report")
            c.setFont("Times-Italic", 14)
            c.drawCentredString(width / 2, height - 1.3 * inch, "Generated by Signal Viewer Application")

            y_position = height - 1.8 * inch

            # Check if there is saved data
            while global_saved_snapshots and global_saved_statistics:
                snapshots = global_saved_snapshots.pop(0)
                statistics = global_saved_statistics.pop(0)

                # Write statistics and add snapshots for each signal
                for signal_name, stats in statistics.items():
                    if stats:
                        c.setStrokeColorRGB(0, 0, 0)
                        c.setLineWidth(1)
                        c.setDash(3, 3)
                        c.rect(margin, y_position - 4.5 * inch, content_width, 4.4 * inch, stroke=True, fill=False)

                        text_x = margin + 0.2 * inch
                        text_y = y_position - 0.5 * inch
                        c.setFont("Times-Bold", 12)
                        c.drawString(text_x, text_y, signal_name)
                        text_y -= line_spacing

                        c.setFont("Times-Roman", 11)
                        for key, value in stats.items():
                            if value is not None:
                                c.drawString(text_x, text_y, f"{key}: {value}")
                                text_y -= line_spacing

                        if signal_name in snapshots:
                            image_x = width - margin - 4 * inch
                            c.drawImage(
                                snapshots[signal_name],
                                image_x,
                                y_position - 4 * inch,
                                width=3.8 * inch,
                                height=3.8 * inch,
                            )

                        y_position -= 5 * inch
                        if y_position < 5 * inch:
                            c.showPage()
                            y_position = height - margin

            # Finalize the PDF and open it
            c.save()
            print(f"Professional report generated at: {report_path}")
            os.system(f"open '{report_path}'")

        except Exception as e:
            self.show_error_message(f"Error generating report: {e}")

    def calculate_statistics(self, signal):
        """
        Calculate basic statistics for a given signal.
        Args:
            signal: The signal data as a numpy array.
        Returns:
            A dictionary containing mean, std, min, max, and duration of the signal.
        """
        if signal is None or len(signal) == 0:
            return {
                "mean": "N/A",
                "std": "N/A",
                "min": "N/A",
                "max": "N/A",
                "duration": "N/A",
            }

        return {
            "mean": round(np.mean(signal), 2),
            "std": round(np.std(signal), 2),
            "min": round(np.min(signal), 2),
            "max": round(np.max(signal), 2),
            "duration": len(signal),  # Assuming duration is the number of data points
        }

    def close_and_unglue(self):
        """
        Close the GlueSignalsWindow and restore the parent state.
        """
        parent = self.parent_window() if self.parent_window else None
        if parent and hasattr(parent, 'unglue_signal'):
            parent.unglue_signal()
        self.close()

    def show_error_message(self, message):
        """
        Display an error message dialog.
        Args:
            message (str): The message to display.
        """
        error_dialog = QtWidgets.QMessageBox(self)
        error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec_()

    # --------------------------------------------------------------------------------------------------------------------------------------
    def setup_ui(self):
        """
        Set up the user interface for the GlueSignalsWindow.
        """
        # Main widget and layout
        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)

        # Set the background color using a stylesheet
        main_widget.setStyleSheet("""
            QWidget {
                background-color: rgb(36, 36, 36);  /* Dark gray background */
                color: white;  /* White text for better contrast */
            }
        """)

        # Create and add the signal plots
        self.create_signal_plot(main_layout, self.signal1, "Signal 1 Portion", "b")
        self.create_signal_plot(main_layout, self.signal2, "Signal 2 Portion", "g")

        # Create and add the glued signal plot
        self.glued_plot_widget = pg.PlotWidget(title="Glued Signal")
        self.glued_plot_widget.setBackground("k")  # Set background color to black
        main_layout.addWidget(self.glued_plot_widget)

        # Add control buttons and input fields
        self.add_controls(main_layout)

        # Set the central widget
        self.setCentralWidget(main_widget)

    def add_controls(self, layout):
        """
        Add controls (buttons and input fields) to the layout.
        Args:
            layout: The layout to add controls to.
        """
        # Create control layouts
        button_layout = QHBoxLayout()
        input_layout = QHBoxLayout()  # For horizontal alignment of input fields

        # Add input fields for gap and interpolation order
        interpolation_label = self.create_label("Interpolation Order:")
        self.interpolation_combo = QComboBox()
        self.interpolation_combo.addItems(['1', '2', '3'])  # Add options for linear, quadratic, and cubic interpolation
        input_layout.addWidget(interpolation_label)
        input_layout.addWidget(self.interpolation_combo)

        gap_label = self.create_label("Gap:")
        self.gap_slider = QSlider(Qt.Horizontal)
        self.gap_slider.setMinimum(1)  # Set minimum value
        self.gap_slider.setMaximum(100)  # Set maximum value
        self.gap_slider.setTickInterval(5)  # Set tick interval
        self.gap_slider.setMaximumWidth(700)
        self.gap_slider.setTickPosition(QSlider.TicksBelow)
        self.gap_slider.valueChanged.connect(self.perform_glue)

        self.gap_slider_value = self.create_label('')
        self.gap_slider_value.setMaximumSize(150, 100)

        input_layout.addWidget(gap_label)
        input_layout.addWidget(self.gap_slider)
        input_layout.addWidget(self.gap_slider_value)

        # Add Glue, Cancel, and Get Report buttons
        back_button = self.create_button("Back", self.close_and_unglue)
        back_button.setFixedSize(150, 40)  # Adjust button size
        save_data_button = self.create_button("Save Data", self.save_data)
        save_data_button.setFixedSize(150, 40)  # Adjust button size
        get_report_button = self.create_button("Get Report", self.generate_report)
        get_report_button.setFixedSize(150, 40)  # Adjust button size

        # Add buttons to the button layout
        button_layout.addWidget(back_button)
        button_layout.addWidget(save_data_button)
        button_layout.addWidget(get_report_button)  # Add Get Report button

        # Add layouts to the main layout
        layout.addLayout(input_layout)
        layout.addLayout(button_layout)

        # Store the Get Report button for potential future use
        self.get_report_button = get_report_button

    def create_button(self, text, callback=None):
        """
        Create a styled QPushButton.
        Args:
            text: The button text.
            callback: The function to call when the button is clicked (optional).
        Returns:
            QPushButton: The created button.
        """
        button = QPushButton(text)
        if callback is not None:  # Only connect if a valid callback is provided
            button.clicked.connect(callback)
        button.setStyleSheet("""
            QPushButton {
                border: 2px solid rgb(255, 255, 255);
                background-color: rgb(36, 36, 36);
                color: white;
            }
            QPushButton:hover {
                background-color: rgb(50, 50, 50);
            }
        """)
        return button

    def create_label(self, text):
        """
        Create a styled QLabel.
        Args:
            text: The label text.
        Returns:
            QLabel: The created label.
        """
        label = QLabel(text)
        label.setStyleSheet("color: white;")
        return label

    def create_signal_plot(self, layout, signal, title, color):
        """
        Create and add a plot with a region selector to the given layout.
        Args:
            layout: The layout to add the plot to.
            signal: The signal data to plot.
            title: The title of the plot.
            color: The color of the plot line.
        """
        plot = pg.PlotWidget(title=title)
        plot.plot(signal, pen=pg.mkPen(color=color, width=2))  # Plot the signal
        region = pg.LinearRegionItem()
        plot.addItem(region)
        layout.addWidget(plot)

        # Store the region item for further use
        if title == "Signal 1 Portion":
            self.region1 = region
        elif title == "Signal 2 Portion":
            self.region2 = region


class Ui_MainWindow(object):
    def __init__(self):

        self.signals_data_ax1 = []
        self.signals_data_ax2 = []
        self.line_plots_ax1 = []
        self.line_plots_ax2 = []
        self.factor = 1
        self.fig_color = (0, 0, 0)
        self.graph_color = (20 / 255, 20 / 255, 20 / 255)
        self.plot_color = (1, 1, 1)
        self.label_color = (1, 1, 1)
        self.backface_color = (0, 0, 0)
        self.is_animating = False
        self.is_second_graph_active = False
        self.is_glued = False
        self.is_merged = False
        self.selector_ax1 = None
        self.selector_ax2 = None
        # self.main_window = None  # You can initialize a placeholder for the main window

    def setupUi(self, MainWindow):
        self.main_window = MainWindow  # Store the MainWindow as a reference

        # Main window setup
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 800)
        font = QtGui.QFont()
        font.setPointSize(11)
        MainWindow.setFont(font)
        MainWindow.setStyleSheet("QWidget { background-color: black; }")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Horizontal line for header separation
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setGeometry(QtCore.QRect(-10, 70, 1300, 2))
        self.line.setStyleSheet("background-color:white;")
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")

        # Header buttons (Home, Signals, Quit)
        self.HomeButton = self.create_button(self.centralwidget, "Home", 790, 18, "rgb(252, 108, 248)")
        self.SignalsButton = self.create_button(self.centralwidget, "Signals", 950, 18, "rgb(147, 247, 167)")
        self.QuitButton = self.create_button(self.centralwidget, "Quit Application", 1120, 18, "rgb(179, 15, 66)")
        self.QuitButton.clicked.connect(QtWidgets.QApplication.quit)

        # Home Page Content Initialization
        self.home_content = QtWidgets.QWidget(self.centralwidget)
        self.home_content.setGeometry(QtCore.QRect(0, 100, 1280, 631))

        # Header icon and title
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 5, 60, 60))
        font.setFamily("Times New Roman")
        self.label.setFont(font)
        self.label.setStyleSheet("color: white;")
        self.label.setPixmap(QtGui.QPixmap("src/sound-wave.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")

        self.HeaderTitleLabel = QtWidgets.QLabel(self.centralwidget)
        self.HeaderTitleLabel.setGeometry(QtCore.QRect(70, 18, 191, 40))
        font.setPointSize(17)
        self.HeaderTitleLabel.setFont(font)
        self.HeaderTitleLabel.setStyleSheet("color: white;")
        self.HeaderTitleLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.HeaderTitleLabel.setObjectName("HeaderTitleLabel")

        # Graph and labels for home page
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(0, 100, 791, 631))
        self.label_3.setPixmap(QtGui.QPixmap("src/Graph.png"))
        self.label_3.setScaledContents(True)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")

        self.HomeTitleLabel = QtWidgets.QLabel(self.centralwidget)
        self.HomeTitleLabel.setGeometry(QtCore.QRect(740, 270, 511, 91))
        font.setPointSize(36)
        font.setBold(True)
        font.setItalic(True)
        self.HomeTitleLabel.setFont(font)
        self.HomeTitleLabel.setStyleSheet("color:white;")
        self.HomeTitleLabel.setWordWrap(True)
        self.HomeTitleLabel.setObjectName("HomeTitleLabel")

        self.HomeSubTitle = QtWidgets.QLabel(self.centralwidget)
        self.HomeSubTitle.setGeometry(QtCore.QRect(740, 350, 461, 101))
        font.setPointSize(14)
        self.HomeSubTitle.setFont(font)
        self.HomeSubTitle.setStyleSheet("color:white;")
        self.HomeSubTitle.setWordWrap(True)
        self.HomeSubTitle.setObjectName("HomeSubTitle")

        self.ProceedSignalsButton = QtWidgets.QPushButton(self.centralwidget)
        self.ProceedSignalsButton.setGeometry(QtCore.QRect(740, 590, 390, 60))
        font.setPointSize(21)
        self.ProceedSignalsButton.setFont(font)
        self.ProceedSignalsButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.ProceedSignalsButton.setStyleSheet("""
            QPushButton {
                border: 2px solid rgb(252, 108, 248);
                padding: 10px;
                color: white;
            }
            QPushButton:hover {
                border-color:rgb(147, 247, 167);
                background-color: rgb(30,30,30);
            }
        """)
        self.ProceedSignalsButton.setObjectName("ProceedSignalsButton")
        self.ProceedSignalsButton.clicked.connect(self.show_signals_page)

        # Signals Page Initialization
        self.signal_content = QtWidgets.QWidget(self.centralwidget)
        self.signal_content.setGeometry(QtCore.QRect(0, 100, 1280, 631))
        self.signal_content.setObjectName("signal_content")
        self.signal_content.hide()

        # Signal selection buttons and images
        self.setup_signal_title_label()
        self.setup_signal_buttons()

        # Individual signal pages (ECG, Circular, etc.)
        self.setup_signal_pages()

        # Menu and status bar
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1280, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        # Connect buttons to page switching functionality
        self.connect_buttons()

        # Set initial active button (Home)
        self.set_active_button_style(self.HomeButton)

        # Add the central widget to the main window
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Multi-Port Signal Viewer"))
        self.HomeButton.setText(_translate("MainWindow", "Home"))
        self.SignalsButton.setText(_translate("MainWindow", "Signals"))
        self.QuitButton.setText(_translate("MainWindow", "Quit Application"))
        self.HeaderTitleLabel.setText(_translate("MainWindow", "Multi-Port Signal Viewer"))
        self.HomeTitleLabel.setText(_translate("MainWindow", "Hello from the Signal Innovators"))
        self.HomeSubTitle.setText(
            "Empowering data, one signal at a time. As a team of passionate problem-solvers, we transform complex signals into meaningful insights, helping you visualize and understand the world of medical data with precision and innovation. Let’s shape the future of signal analysis together, one breakthrough at a time.")
        self.ProceedSignalsButton.setText(_translate("MainWindow", "Proceed to Signal"))

    def create_button(self, parent, text, x, y, hover_color):
        # Helper function to create and style a button
        button = QtWidgets.QPushButton(parent)
        button.setGeometry(QtCore.QRect(x, y, 140, 40))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(17)
        button.setFont(font)
        button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        button.setStyleSheet(f"""
            QPushButton {{
                border: none;
                padding: 10px;
                color: white;
                border-bottom: 2px solid transparent;
            }}
            QPushButton:hover {{
                border-bottom-color: {hover_color};
                color: {hover_color};
            }}
        """)
        button.setText(text)
        return button

    def create_signal_button_with_label(self, parent, image_path, button_text, x, y):
        # Create a label for the image
        image_label = QtWidgets.QLabel(parent)
        image_label.setGeometry(QtCore.QRect(x, y, 270, 260))  # Set geometry for image label
        image_label.setPixmap(QtGui.QPixmap(image_path))  # Set the image from the provided path
        image_label.setScaledContents(True)  # Scale the image to fit the label
        image_label.setAlignment(QtCore.Qt.AlignCenter)  # Center the image
        image_label.setObjectName(f"{button_text}_image_label")  # Assign object name based on the button text

        # Create the button below the label
        button = QtWidgets.QPushButton(parent)
        button.setGeometry(QtCore.QRect(x, y + 260, 270, 60))  # Place button directly below the label
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(25)
        button.setFont(font)
        button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        button.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 10px;
                color: rgb(184, 184, 184);
                border: 2px solid rgb(184, 184, 184);
                background-color: rgb(20, 20, 20);
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 80, 200);
            }
        """)
        button.setText(button_text)
        button.setObjectName(f"{button_text}_button")  # Assign object name based on the button text

        return image_label, button

    def add_back_button(self, parent_widget, icon_path="src/backArrow.png"):
        # Create and configure the back button for a given parent widget
        back_button = QtWidgets.QPushButton(parent_widget)
        back_button.setMaximumSize(QSize(150, 60))
        # Set back button icon
        icon = QtGui.QIcon()
        icon.addFile(icon_path, QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        back_button.setIcon(icon)
        back_button.setIconSize(QtCore.QSize(80, 80))
        back_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        back_button.raise_()

        return back_button

    def handle_back_button(self):
        # Show the signals page
        self.show_signals_page()

    def handle_rectangular_back_button(self):
        self.reset_rectangular_signals()
        # Show the signals page
        self.show_signals_page()

    def create_signal_page(self, parent=None):
        # Create a signal-specific content page
        signal_page = QtWidgets.QLabel(parent)
        signal_page.setGeometry(QtCore.QRect(0, 100, 1280, 631))
        signal_page.hide()
        return signal_page

    def setup_signal_pages(self):
        # Setup signal content (ECG, Circular, EEG, RTS) and their back buttons
        self.rectangular_content = self.create_signal_page(self.centralwidget)

        self.RTS_content = self.create_signal_page(self.centralwidget)

        self.circular_content = self.create_signal_page(self.centralwidget)

    def setup_signal_title_label(self):
        # Set up the title label for the signal page
        self.SignalTitleLabel = QtWidgets.QLabel(self.signal_content)
        self.SignalTitleLabel.setGeometry(QtCore.QRect(270, 80, 740, 91))
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(80)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.SignalTitleLabel.setFont(font)
        self.SignalTitleLabel.setStyleSheet("color: white;")
        self.SignalTitleLabel.setAlignment(QtCore.Qt.AlignCenter)  # Center the text horizontally and vertically
        self.SignalTitleLabel.setObjectName("SignalTitleLabel")
        self.SignalTitleLabel.setText("Pick a Type of Signal!")  # Set the default text

    def setup_signal_buttons(self):
        # Set up labels and buttons for signals page
        self.rectangular_image, self.rectuangular_Button = self.create_signal_button_with_label(self.signal_content,
                                                                                                "src/rectangular-signal.png",
                                                                                                "Rectangular Signal",
                                                                                                118, 300)
        self.RTS_image, self.RTS_Button = self.create_signal_button_with_label(self.signal_content, "src/weather.png",
                                                                               "Real Time Signal", 505, 300)
        self.circular_image, self.circular_Button = self.create_signal_button_with_label(self.signal_content,
                                                                                         "src/PolarPlot.png",
                                                                                         "Circular Signal", 893, 300)
        # Create and configure overlay buttons
        self.create_overlay_button("rectangular_overlay", 118, 300, self.rectuangular_Button.click)
        self.create_overlay_button("RTS_overlay", 505, 300, self.RTS_Button.click)
        self.create_overlay_button("circular_overlay", 893, 300, self.circular_Button.click)

    def create_overlay_button(self, name, x, y, callback):
        # Create an overlay button with semi-transparent background and cursor
        overlay_button = QtWidgets.QPushButton(self.signal_content)
        overlay_button.setGeometry(QtCore.QRect(x, y, 270, 260))
        overlay_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        overlay_button.setStyleSheet("background-color:rgba(20,20,20,200);")
        overlay_button.setObjectName(name)
        overlay_button.clicked.connect(callback)
        return overlay_button

    def connect_buttons(self):
        # Connect button clicks to page-switching methods
        self.HomeButton.clicked.connect(self.show_home_page)
        self.SignalsButton.clicked.connect(self.show_signals_page)

        self.rectuangular_Button.clicked.connect(self.show_rectangular_page)
        self.circular_Button.clicked.connect(self.show_circular_page)
        self.RTS_Button.clicked.connect(self.show_RTS_page)

    def set_active_button_style(self, active_button):
        # Style the active button to show which page is selected
        self.HomeButton.setStyleSheet(
            "QPushButton { padding: 10px; color: white; border-bottom: none; }")
        self.SignalsButton.setStyleSheet(
            "QPushButton { padding: 10px; color: white; border-bottom: none; }")

        if active_button == self.HomeButton:
            active_style = "QPushButton { color: rgb(252, 108, 248); border-bottom: 2px solid rgb(252, 108, 248); }"
        elif active_button == self.SignalsButton:
            active_style = "QPushButton { color: rgb(147, 247, 167); border-bottom: 2px solid rgb(147, 247, 167); }"
        active_button.setStyleSheet(active_style)

    def show_home_page(self):
        self.home_content.show()
        self.signal_content.hide()
        self.hide_all_signal_pages()
        self.set_active_button_style(self.HomeButton)

    def show_signals_page(self):
        self.home_content.hide()
        self.signal_content.show()
        self.hide_all_signal_pages()
        self.set_active_button_style(self.SignalsButton)

    def show_rectangular_page(self):
        self.signal_content.hide()
        self.hide_all_signal_pages(exclude="Rectangular")  # Ensure all other signal pages are hidden
        self.rectangular_content.show()  # Show the EEG content page
        self.setup_rectangular_page()  # Initialize the EEG page (plotting, buttons, etc.)

    def show_RTS_page(self):
        self.signal_content.hide()
        self.hide_all_signal_pages(exclude="RTS")
        self.RTS_content.show()
        self.setup_RTS_page()

    def show_circular_page(self):
        self.signal_content.hide()
        self.hide_all_signal_pages(exclude="Circular")
        self.circular_content.show()
        self.setup_circular_page()

    def hide_all_signal_pages(self, exclude=None):
        # Helper method to hide all signal pages except the one specified
        if exclude != "Rectangular":
            self.rectangular_content.hide()
        if exclude != "Circular":
            self.circular_content.hide()
        if exclude != "RTS":
            self.RTS_content.hide()

    '''---------------------------------------------------------------------------------------------------------------------------------------'''

    def setup_rectangular_page(self):
        self.current_index_1 = 0  # Initialize index for plot 1
        self.current_index_2 = 0  # Initialize index for plot 2
        self.speeds = [0.5, 1, 2, 4, 16, 32]  # Speed multipliers
        self.current_speed_index = 1  # Default to 1x speed (index of 1)
        self.plot_colors = ['r', 'y', 'c', 'm', 'k', 'g', 'b']  # List of colors
        self.current_color_index = 0  # Start with the first color in the list
        self.signal1 = None  # Initialize signal1
        self.signal2 = None  # Initialize signal2

        if not hasattr(self, 'rectangular_initialized') or not self.rectangular_initialized:
            print("Setting up Rectangular page...")  # Debug

            # Create buttons for the Rectangular page
            play_pause_button_1 = QtWidgets.QPushButton("Play ▶", self.rectangular_content)
            play_pause_button_2 = QtWidgets.QPushButton("Play ▶", self.rectangular_content)
            unified_play_pause_button = QtWidgets.QPushButton("Play Both ▶", self.rectangular_content)
            reset_button = QtWidgets.QPushButton("Reset Signal", self.rectangular_content)
            speed_button = QtWidgets.QPushButton("1X", self.rectangular_content)
            change_signal_01 = QtWidgets.QPushButton("Signal 01", self.rectangular_content)
            change_signal_02 = QtWidgets.QPushButton("Signal 02", self.rectangular_content)
            change_dynamic_signal = QtWidgets.QPushButton("Change Signal", self.rectangular_content)
            link_button = QtWidgets.QPushButton("Unink", self.rectangular_content)
            add_signal_button = QtWidgets.QPushButton("Add Signal", self.rectangular_content)
            add_signal_graph01 = QtWidgets.QPushButton("Graph 01", self.rectangular_content)
            add_signal_graph02 = QtWidgets.QPushButton("Graph 02", self.rectangular_content)
            merge_button = QtWidgets.QPushButton("Merge", self.rectangular_content)
            glue_button = QtWidgets.QPushButton("Glue", self.rectangular_content)

            # Initialize PyQtGraph Rectangular Graph
            self.initialize_pyqtgraph_rectangular_graph(
                content_widget=self.rectangular_content,
                play_pause_button_1=play_pause_button_1,
                play_pause_button_2=play_pause_button_2,
                reset_button=reset_button,
                link_button=link_button,
                unified_play_pause_button=unified_play_pause_button,
                add_signal_button=add_signal_button,
                add_signal_graph01=add_signal_graph01,
                add_signal_graph02=add_signal_graph02,
                merge_button=merge_button,
                glue_button=glue_button,
                speed_button=speed_button,
                change_dynamic_signal=change_dynamic_signal,
                change_signal_01=change_signal_01,
                change_signal_02=change_signal_02,
                signal_1_label="Rectangular Signal",
                signal_2_label="Rectangular Signal 2"
            )

            # Link button function
            self.linked_mode = True  # Initial state of link button
            link_button.clicked.connect(
                lambda: self.toggle_link_mode(
                    link_button,
                    play_pause_button_1,
                    play_pause_button_2,
                    unified_play_pause_button
                )
            )

            # Load signals for both plots
            self.data_1 = np.loadtxt("Data/Rectangular Data/Cosine/signal_2Hz_100Hz.csv", delimiter=',', skiprows=1)
            self.time_data_1 = self.data_1[:, 0]
            self.amplitude_data_1 = self.data_1[:, 1]

            self.data_2 = np.loadtxt("Data/Rectangular Data/Cosine/signal_2Hz_6Hz.csv", delimiter=',', skiprows=1)
            self.time_data_2 = self.data_2[:, 0]
            self.amplitude_data_2 = self.data_2[:, 1]

            # Initialize timers for each plot
            self.timer_1 = QTimer()
            self.timer_2 = QTimer()

            # Connect play/pause buttons to timer start/stop
            play_pause_button_1.clicked.connect(lambda: self.toggle_play_pause(
                self.timer_1,
                play_pause_button_1,
                self.pg_plot_widget_1,
                self.time_data_1,
                self.amplitude_data_1,
                'current_index_1'
            ))

            play_pause_button_2.clicked.connect(lambda: self.toggle_play_pause(
                self.timer_2,
                play_pause_button_2,
                self.pg_plot_widget_2,
                self.time_data_2,
                self.amplitude_data_2,
                'current_index_2'
            ))

            unified_play_pause_button.clicked.connect(
                lambda: self.toggle_play_pause_both(
                    [self.timer_1, self.timer_2], unified_play_pause_button
                )
            )
            speed_button.clicked.connect(lambda: self.toggle_speed(speed_button))
            self.timer_1.timeout.connect(lambda: setattr(self, 'current_index_1',
                                                         self.update_plot(self.pg_plot_widget_1, self.time_data_1,
                                                                          self.amplitude_data_1, self.current_index_1)))
            self.timer_2.timeout.connect(lambda: setattr(self, 'current_index_2',
                                                         self.update_plot(self.pg_plot_widget_2, self.time_data_2,
                                                                          self.amplitude_data_2, self.current_index_2)))

            self.rectangular_initialized = True

    def initialize_pyqtgraph_rectangular_graph(self, content_widget, play_pause_button_1, play_pause_button_2,
                                               reset_button, link_button, unified_play_pause_button, add_signal_button,
                                               add_signal_graph01, add_signal_graph02, merge_button, glue_button,
                                               speed_button, change_signal_01, change_signal_02, change_dynamic_signal,
                                               signal_1_label="Signal 1", signal_2_label="Signal 2",
                                               signal_3_label="Glued Signal"):
        """Initialize the PyQtGraph-based rectangular graph interface."""
        self.pg_plot_widget_1 = pg.PlotWidget(background="k")
        self.pg_plot_widget_2 = pg.PlotWidget(background="k")

        # Configure plots using a helper function
        self.configure_plot(self.pg_plot_widget_1, signal_1_label)
        self.configure_plot(self.pg_plot_widget_2, signal_2_label)

        # Layout for the plots
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.pg_plot_widget_1)
        graph_layout.addWidget(self.pg_plot_widget_2)

        # Stretch the plots to take full height within their space
        graph_layout.setStretch(0, 1)  # Stretch for the first plot
        graph_layout.setStretch(1, 1)  # Stretch for the second plot
        graph_layout.setStretch(2, 2)  # Stretch for the third (larger) plot

        # Remove margins and spacing in the graph layout
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(0)

        # Button layout
        button_layout = QVBoxLayout()
        self.setup_buttons(button_layout, unified_play_pause_button, play_pause_button_1, play_pause_button_2,
                           link_button, reset_button, change_signal_01, change_signal_02, change_dynamic_signal,
                           add_signal_graph01, add_signal_graph02, merge_button, glue_button, speed_button,
                           add_signal_button)

        # Remove margins and spacing in the button layout
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)  # Small spacing for buttons

        # Store references in the dictionary for later use
        self.buttons = {
            'play_pause_button_1': play_pause_button_1,
            'play_pause_button_2': play_pause_button_2,
            'unified_play_pause_button': unified_play_pause_button,
            'reset_button': reset_button,
            'link_button': link_button,
            'speed_button': speed_button,
            'change_signal_01': change_signal_01,
            'change_signal_02': change_signal_02,
            'change_dynamic_signal': change_dynamic_signal,
            'add_signal_graph01': add_signal_graph01,
            'add_signal_graph02': add_signal_graph02,
            'merge_button': merge_button,
            'glue_button': glue_button,
            'add_signal_button': add_signal_button
        }

        # Connect reset button to reset functionality
        reset_button.clicked.connect(self.reset_signals)

        # Initially hide individual play/pause buttons and signal graph buttons
        self.hide_buttons(['play_pause_button_1', 'play_pause_button_2', 'add_signal_graph01', 'add_signal_graph02',
                           'change_signal_01', 'change_signal_02'])

        # Connect the "Add Signal" button to show the new buttons
        add_signal_button.clicked.connect(self.toggle_add_signal_mode)

        # Correct the signal buttons to load files
        add_signal_graph01.clicked.connect(lambda: self.load_rectangular_signal_file(1))
        add_signal_graph02.clicked.connect(lambda: self.load_rectangular_signal_file(2))

        # Connect change signal buttons to file dialogs
        change_signal_01.clicked.connect(lambda: self.load_dynamic_signal(1))
        change_signal_02.clicked.connect(lambda: self.load_dynamic_signal(2))

        merge_button.clicked.connect(self.toggle_merge)
        glue_button.clicked.connect(self.toggle_glue)
        change_dynamic_signal.clicked.connect(self.toggle_change_signal_mode)

        # Combine layouts into the main content widget
        layout = QtWidgets.QHBoxLayout(content_widget)

        # Add the graph layout and button layout with vertical stretch
        layout.addLayout(graph_layout, stretch=4)  # Graph layout gets more space
        layout.addLayout(button_layout, stretch=1)  # Button layout gets less space

        # Set the content widget to expand and occupy available space
        content_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def reset_signals(self):
        # Stop the timers for both signals
        self.timer_1.stop()
        self.timer_2.stop()

        # Clear the plot widgets and delete lines if necessary
        self.clear_and_prepare_widgets()

        # Reset indices and button texts
        self.current_index_1 = 0
        self.current_index_2 = 0
        self.reset_button_texts()

        # Debug print to ensure this part runs
        print("Reset complete. Setting up plot connections...")

        # Reconnect timers to update functions
        self.setup_timer_connections()

    def clear_and_prepare_widgets(self):
        # Clear plots based on merge state and delete lines
        if self.is_merged:
            self.pg_plot_widget_1.clear()
            self.delete_lines(self.pg_plot_widget_1)
        else:
            self.pg_plot_widget_1.clear()
            self.pg_plot_widget_2.clear()
            self.delete_lines(self.pg_plot_widget_1)
            self.delete_lines(self.pg_plot_widget_2)

        # Reinitialize lines if they do not exist
        self.reinitialize_lines()

    def delete_lines(self, widget):
        if hasattr(widget, "line_1"):
            del widget.line_1
        if hasattr(widget, "line_2"):
            del widget.line_2

    def reinitialize_lines(self):
        if not hasattr(self.pg_plot_widget_1, "line_1"):
            self.pg_plot_widget_1.line_1 = self.pg_plot_widget_1.plot([], [],
                                                                      pen=pg.mkPen(self.plot_colors[0], width=2))
        if not hasattr(self.pg_plot_widget_2, "line_2"):
            self.pg_plot_widget_2.line_2 = self.pg_plot_widget_2.plot([], [],
                                                                      pen=pg.mkPen(self.plot_colors[1], width=2))

    def reset_button_texts(self):
        self.buttons['play_pause_button_1'].setText("Play ▶")
        self.buttons['play_pause_button_2'].setText("Play ▶")
        self.buttons['unified_play_pause_button'].setText("Play Both ▶")

    def setup_timer_connections(self):
        self.timer_1.timeout.connect(
            lambda: self.update_plot(self.pg_plot_widget_1, self.time_data_1, self.amplitude_data_1,
                                     self.current_index_1))
        self.timer_2.timeout.connect(
            lambda: self.update_plot(self.pg_plot_widget_2, self.time_data_2, self.amplitude_data_2,
                                     self.current_index_2))
        print("Timer connections set up.")

    def update_plot(self, plot_widget, time_data, amplitude_data, current_index, max_points=5):
        """
        Incrementally update the plot without redrawing everything.
        Args:
            plot_widget: The plot widget to update.
            time_data: The time data for the signal.
            amplitude_data: The amplitude data for the signal.
            current_index: The current index of the data being drawn.
            max_points: Number of points to draw per update.
        """
        # Ensure current_index is treated as an integer
        current_index = int(current_index)

        # Choose line color based on the widget
        if plot_widget == self.pg_plot_widget_1:
            line_color = 'b'  # Blue color for Signal 1
        elif plot_widget == self.pg_plot_widget_2:
            line_color = 'g'  # Green color for Signal 2
        else:
            line_color = 'r'  # Red color for any additional widgets

        # Initialize lines if they do not exist
        if not hasattr(plot_widget, "line_1"):
            plot_widget.line_1 = plot_widget.plot([], [], pen=pg.mkPen(line_color, width=2))
        if not hasattr(plot_widget, "line_2") and self.is_merged:
            plot_widget.line_2 = plot_widget.plot([], [], pen=pg.mkPen('y', width=2))  # Yellow color for merged line

        # Calculate the end index for plotting
        end_index = min(current_index + max_points, len(time_data))

        # Update the plot data
        plot_widget.line_1.setData(time_data[:end_index], amplitude_data[:end_index])

        # If merged, update both signals on the same widget
        if self.is_merged and hasattr(plot_widget, "line_2"):
            # Ensure the second signal exists and matches the time data
            if hasattr(self, "time_data_2") and hasattr(self, "amplitude_data_2"):
                plot_widget.line_2.setData(self.time_data_2[:end_index], self.amplitude_data_2[:end_index])

        # Determine if we need to update the current index or stop updating
        if end_index >= len(time_data):
            # Stop updating if at the end of the data
            print(f"Completed plotting for {plot_widget}.")
            return end_index  # You might handle this to deactivate the timer or button
        else:
            # Continue plotting
            return end_index  # Update the current index for the next timeout

    def toggle_play_pause_both(self, timers, button):
        """
        Toggle play/pause for multiple timers.
        Args:
            timers: List of timers to control.
            button: The unified play/pause button.
        """
        if all(timer.isActive() for timer in timers):
            # If all timers are active, stop them
            for timer in timers:
                timer.stop()
            button.setText("Play Both ▶")
            self.buttons['play_pause_button_1'].setText("Pause")
            self.buttons['play_pause_button_2'].setText("Pause")
        else:
            # If any timer is inactive, start all timers with the same interval
            new_interval = int(100 / self.speeds[self.current_speed_index])
            all_complete = True
            for timer in timers:
                timer.setInterval(new_interval)
                timer.start()
                # Determine button text based on whether the data is fully plotted
                if getattr(self, 'current_index_1') >= len(self.time_data_1):
                    self.buttons['play_pause_button_1'].setText("Finished")
                else:
                    self.buttons['play_pause_button_1'].setText("Playing…")

                if getattr(self, 'current_index_2') >= len(self.time_data_2):
                    self.buttons['play_pause_button_2'].setText("Finished")
                else:
                    self.buttons['play_pause_button_2'].setText("Playing…")

                # Check if the timer's corresponding plot has finished
                if getattr(self, 'current_index_' + ('1' if timer == self.timer_1 else '2')) < len(
                        getattr(self, 'time_data_' + ('1' if timer == self.timer_1 else '2'))):
                    all_complete = False

            if all_complete:
                button.setText("Finished")  # If all data is fully plotted, show "Finished"
            else:
                button.setText("Playing…")  # If not all data is plotted, show "Playing…"

    def toggle_play_pause(self, timer, button, plot_widget, time_data, amplitude_data, current_index_key):
        """
        Toggle the play/pause state of a timer.
        Args:
            timer: QTimer object to control.
            button: QPushButton object associated with the timer.
            plot_widget: The plot widget to redraw on play.
            time_data: Time data for the signal.
            amplitude_data: Amplitude data for the signal.
            current_index_key: Attribute key to keep track of the current index (e.g., 'current_index_1').
        """
        if timer.isActive():
            timer.stop()
            # Update button text to "Play ▶" when the timer stops
            button.setText("Play ▶")
        else:
            # Start the timer and check if the data has been fully plotted
            timer.start(int(100 / self.speeds[self.current_speed_index]))
            if getattr(self, current_index_key) >= len(time_data):
                # If the end of data is reached, update the button text to "Finished"
                button.setText("Finished")
            else:
                # If not fully plotted, set the button to "Pause ▶"
                button.setText("Pause ▶")

            # Connect timer to the update function based on the merge state
            if self.is_merged:
                # Use the first plot widget for both signals when merged
                self.timer_1.timeout.connect(lambda: self.update_plot(self.pg_plot_widget_1, self.time_data_1,
                                                                      self.amplitude_data_1, self.current_index_1))
                self.timer_2.timeout.connect(lambda: self.update_plot(self.pg_plot_widget_1, self.time_data_2,
                                                                      self.amplitude_data_2, self.current_index_2))
            else:
                # Update only the respective plot widget
                timer.timeout.connect(lambda: setattr(
                    self, current_index_key,
                    self.update_plot(
                        plot_widget,
                        time_data,
                        amplitude_data,
                        getattr(self, current_index_key)
                    )
                ))

                # If the specific plot widget is the first one, ensure the second widget updates independently
                if plot_widget == self.pg_plot_widget_1:
                    self.timer_2.timeout.connect(lambda: self.update_plot(self.pg_plot_widget_2, self.time_data_2,
                                                                          self.amplitude_data_2, self.current_index_2))

    def load_dynamic_signal(self, signal_number):
        """
        Open a file dialog to select a new signal file and update the plot for the given signal.
        Args:
            signal_number (int): The signal number (1 or 2) to update.
        """
        try:
            # Open the file dialog
            options = QtWidgets.QFileDialog.Options()
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                None,
                "Select Signal File",
                "",
                "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)",
                options=options
            )

            if not file_path:
                print("File selection canceled.")
                return  # Exit if no file is selected

            # Load the selected signal file
            data = np.loadtxt(file_path, delimiter=',', skiprows=1)
            time_data, amplitude_data = data[:, 0], data[:, 1]

            # Update the appropriate signal and plot
            if signal_number == 1:
                self.time_data_1 = time_data
                self.amplitude_data_1 = amplitude_data
                self.current_index_1 = 0  # Reset index
                self.update_plot(self.pg_plot_widget_1, self.time_data_1, self.amplitude_data_1, self.current_index_1)
                print(f"Signal 1 successfully updated with file: {file_path}")
            elif signal_number == 2:
                self.time_data_2 = time_data
                self.amplitude_data_2 = amplitude_data
                self.current_index_2 = 0  # Reset index
                self.update_plot(self.pg_plot_widget_2, self.time_data_2, self.amplitude_data_2, self.current_index_2)
                print(f"Signal 2 successfully updated with file: {file_path}")
            else:
                raise ValueError("Invalid signal number. Please use 1 or 2.")

            # Toggle back to default state after a successful update
            self.toggle_change_signal_mode()

        except ValueError as ve:
            self.show_error_message(f"Value Error: {ve}")
        except Exception as e:
            self.show_error_message(f"Error loading file: {e}")

    def load_rectangular_signal_file(self, graph_num):
        """
        Open a file dialog to load the signal data for the selected graph.
        Args:
            graph_num (int): The graph number (1 or 2) to associate the loaded signal with.
        """
        try:
            options = QFileDialog.Options()

            # Use the main window as the parent for the file dialog
            parent_widget = self.main_window if hasattr(self, 'main_window') else self

            # Open file dialog to select the signal file
            file_name, _ = QFileDialog.getOpenFileName(
                parent_widget,
                "Select Rectangular Signal File",
                "",
                "CSV and TXT Files (*.csv *.txt);;All Files (*)",
                options=options
            )

            if not file_name:
                return  # Exit if no file is selected

            # Load and process the signal based on the selected graph
            if graph_num == 1:
                self.load_and_process_rectangular_signal(file_name, self.pg_plot_widget_1)
                self.load_rectangular_signal_data(file_name, 'signal1', 'current_index_1')
            elif graph_num == 2:
                self.load_and_process_rectangular_signal(file_name, self.pg_plot_widget_2)
                self.load_rectangular_signal_data(file_name, 'signal2', 'current_index_2')

            # Restore buttons after successful load
            self.restore_buttons()

        except Exception as e:
            print(f"Error loading rectangular signal file: {e}")
            self.show_error_message(f"Error loading rectangular signal file: {e}")

    def load_rectangular_signal_data(self, file_path, signal_data_attr, index_attr, is_static=False):
        """
        Load the rectangular signal data into the specified attribute based on the file type.
        Args:
            file_path (str): Path to the rectangular signal file.
            signal_data_attr (str): Attribute name to store the loaded signal data.
            index_attr (str): Attribute name to reset and store the current index for the signal.
            is_static (bool): Flag to determine if the loaded data is static and should not reset indices.
        """
        try:
            _, file_extension = os.path.splitext(file_path)

            if file_extension == ".txt":
                # Load TXT file assuming whitespace-separated values
                signal_data = np.loadtxt(file_path)
            elif file_extension == ".csv":
                # Load CSV file assuming signal is in the second column
                data = np.loadtxt(file_path, delimiter=',', skiprows=1)
                signal_data = data[:, 1]  # Select the second column
            elif file_extension == ".edf":
                # Load EDF file using pyEDFlib
                with pyedflib.EdfReader(file_path) as f:
                    n_signals = f.signals_in_file
                    signal_data = np.zeros((n_signals, f.getNSamples()[0]))
                    for i in range(n_signals):
                        signal_data[i, :] = f.readSignal(i)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

            # Assign the loaded data and reset the index if not static
            setattr(self, signal_data_attr, signal_data)
            if not is_static:
                setattr(self, index_attr, 0)
            print(f"Successfully loaded rectangular signal data from {file_path} into {signal_data_attr}.")

        except Exception as e:
            print(f"Error processing rectangular signal data: {e}")
            self.show_error_message(f"Error processing rectangular signal data: {e}")

    def load_and_process_rectangular_signal(self, file_name, plot_widget):
        """
        Load and plot rectangular signal data on the given widget without affecting existing dynamic plots.
        This function will add the plots as static layers that do not interfere with the dynamic plot indices or states.
        """
        try:
            # Load the signal data from the file
            data = np.loadtxt(file_name, delimiter=',', skiprows=1)
            if data.ndim != 2 or data.shape[1] != 2:
                raise ValueError("File must contain exactly two columns: Time and Signal.")

            time, amplitude = data[:, 0], data[:, 1]
            color = self.plot_colors[self.current_color_index]

            # Create a new plot data item for the static signal
            static_plot_item = pg.PlotDataItem(time, amplitude, pen=pg.mkPen(color=color, width=2))

            # Add the static plot item to the widget
            plot_widget.addItem(static_plot_item)

            # Update the color index for subsequent plots, but do not reset or affect dynamic plots
            self.current_color_index = (self.current_color_index + 1) % len(self.plot_colors)

            print("Static signal plotted successfully from " + file_name)

        except Exception as e:
            print(f"Error in loading and processing static signal: {e}")

    def update_plot(self, plot_widget, time_data, amplitude_data, current_index, max_points=5):
        """
        Incrementally update the plot without redrawing everything.
        Args:
            plot_widget: The plot widget to update.
            time_data: The time data for the signal.
            amplitude_data: The amplitude data for the signal.
            current_index: The current index of the data being drawn.
            max_points: Number of points to draw per update.
        """
        # Declare signals (signal1 and signal2) dynamically based on the widget
        if plot_widget == self.pg_plot_widget_1:
            self.dynamic_signal_01 = amplitude_data
            line_color = 'b'  # Assign color for Signal 1 (Green)
        elif plot_widget == self.pg_plot_widget_2:
            self.dynamic_signal_02 = amplitude_data
            line_color = 'g'  # Assign color for Signal 2 (Blue)
        else:
            line_color = 'r'  # Default color for any additional widgets

        # Create references to the line plots if not already present
        if not hasattr(plot_widget, "line_1"):
            plot_widget.line_1 = plot_widget.plot([], [], pen=pg.mkPen(line_color, width=2))  # Initialize first line
        if not hasattr(plot_widget, "line_2"):
            plot_widget.line_2 = plot_widget.plot([], [], pen=pg.mkPen('y', width=2))  # Initialize second line (Yellow)

        # Incrementally update the plot data
        end_index = min(current_index + max_points, len(time_data))

        # Update data for line 1 (first signal)
        plot_widget.line_1.setData(time_data[:end_index], amplitude_data[:end_index])

        # If merged, update both signals (line_1 and line_2) on the same widget
        if self.is_merged:
            # Ensure the second signal exists and has matching time data
            if hasattr(self, "time_data_2") and hasattr(self, "amplitude_data_2"):
                plot_widget.line_2.setData(self.time_data_2[:end_index], self.amplitude_data_2[:end_index])

        # Update the current index
        if current_index >= len(time_data) - 1:
            return current_index  # Stop updating if at the end
        else:
            return end_index  # Return the next index to plot

    def toggle_change_signal_mode(self):
        """
        Toggle the visibility and state for the 'Change Signal' functionality.
        """
        self.toggle_button_mode(
            button_key='change_dynamic_signal',
            active_text="Cancel",
            inactive_text="Change Signal",
            buttons_to_hide=[
                'unified_play_pause_button', 'reset_button', 'link_button', 'merge_button', 'glue_button',
                'speed_button', 'add_signal_button'
            ],
            buttons_to_show=['change_signal_01', 'change_signal_02']
        )

    def toggle_add_signal_mode(self):
        """
        Toggle the visibility and state for the 'Add Signal' functionality.
        """
        self.toggle_button_mode(
            button_key='add_signal_button',
            active_text="Cancel",
            inactive_text="Add Signal",
            buttons_to_hide=[
                'unified_play_pause_button', 'reset_button', 'link_button', 'merge_button', 'glue_button',
                'speed_button', 'change_dynamic_signal'
            ],
            buttons_to_show=['add_signal_graph01', 'add_signal_graph02']
        )

    def toggle_merge(self):
        """
        Merge or unmerge the two signals based on the current state.
        """
        if self.is_merged:  # If already merged, unmerge it
            self.unmerge_signals()
        else:  # If not merged, merge the signals
            self.merge_signals()

    def merge_signals(self):
        """
        Perform the merge action: hide one graph, create merged plot, and update button text.
        """
        # Hide the second graph (graph 2)
        self.pg_plot_widget_2.hide()

        # Create a new plot widget for the merged graph
        self.merged_plot_widget = pg.PlotWidget(background="k")
        self.configure_plot(self.merged_plot_widget, "Merged Signal")

        # Use the layout that holds the content widgets (e.g., `content_layout`)
        content_layout = self.buttons.get('content_layout', None)  # Or whatever layout holds the plots
        if content_layout:
            content_layout.addWidget(self.merged_plot_widget)  # Add merged plot widget to the layout

        # Merge the data from both signals
        merged_time = np.concatenate((self.time_data_1, self.time_data_2))
        merged_amplitude = np.concatenate((self.amplitude_data_1, self.amplitude_data_2))

        # Plot the merged data on the new plot widget
        self.merged_plot_widget.plot(merged_time, merged_amplitude, pen=pg.mkPen(color='w', width=2))

        # Reset the current color index for the merged plot
        self.current_color_index = (self.current_color_index + 1) % len(self.plot_colors)

        # Synchronize play/pause buttons for both signals (since they're now merged)
        self.buttons['unified_play_pause_button'].setText("Play ▶")

        # Update merge button text to "Unmerge"
        self.buttons['merge_button'].setText("Unmerge")

        # Set the merge state to True
        self.is_merged = True

    def unmerge_signals(self):
        """
        Unmerge the signals and restore the original state.
        """
        # Ensure the second plot widget is visible again
        self.pg_plot_widget_2.show()

        # Remove the merged plot widget from the layout and clear it
        if hasattr(self, 'merged_plot_widget'):
            self.merged_plot_widget.clear()
            content_layout = self.buttons.get('content_layout', None)  # Or whatever layout holds the plots
            if content_layout and self.merged_plot_widget in content_layout.children():
                content_layout.removeWidget(self.merged_plot_widget)
            self.merged_plot_widget.setParent(None)

        # Repopulate the original plots with their respective data
        self.pg_plot_widget_1.plot(self.time_data_1, self.amplitude_data_1, pen=pg.mkPen(color='b', width=2),
                                   clear=True)
        self.pg_plot_widget_2.plot(self.time_data_2, self.amplitude_data_2, pen=pg.mkPen(color='g', width=2),
                                   clear=True)

        # Set both plots to have the same minimum size to ensure equal height
        self.pg_plot_widget_1.setMinimumSize(500, 300)  # Adjust this to your preferred size (width, height)
        self.pg_plot_widget_2.setMinimumSize(500, 300)  # Same height as the first graph

        # Ensure both widgets have the same size policy to expand equally
        self.pg_plot_widget_1.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.pg_plot_widget_2.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Manually update layout to ensure both graphs have the same height
        self.rectangular_content.layout().update()
        self.rectangular_content.layout().invalidate()

        # Reset the unified play/pause button text
        self.buttons['unified_play_pause_button'].setText("Play Both ▶")

        # Update merge button text back to "Merge"
        self.buttons['merge_button'].setText("Merge")

        # Set the merge state to False
        self.is_merged = False

    def toggle_glue(self):
        """
        Toggle the glued state and manage the glue/unglue functionality for the plots.
        """
        # if self.is_glued:
        #     self.unglue_signal()  # Unglue if currently glued
        # else:
        #     self.glue_signal()  # Glue if currently unglued
        self.is_glued = not self.is_glued
        # Open the GlueSignalsWindow with signal data and set self as the parent
        self.glue_window = GlueSignalsWindow(self.dynamic_signal_01, self.dynamic_signal_02, parent=self.main_window)
        self.glue_window.show()

    def toggle_link_mode(self, link_button, button_1, button_2, unified_button):
        self.linked_mode = not self.linked_mode  # Toggle the linked mode state

        if self.linked_mode:
            # If linked mode is activated
            link_button.setText("Unlink")
            button_1.hide()
            button_2.hide()
            unified_button.show()

            # Ensure timers are synchronized
            if self.timer_1.isActive() or self.timer_2.isActive():
                unified_button.setText("Pause Both")
            else:
                unified_button.setText("Play Both ▶")
        else:
            # If linked mode is deactivated
            link_button.setText("Link")
            button_1.show()
            button_2.show()
            unified_button.hide()

    def toggle_speed(self, speed_button):
        """
        Toggle the speed of the signal visualization.

        Args:
            speed_button: The QPushButton controlling speed.
        """
        # Cycle through the speeds
        self.current_speed_index = (self.current_speed_index + 1) % len(self.speeds)
        current_speed = self.speeds[self.current_speed_index]

        # Update the button text
        speed_button.setText(f"{current_speed}X")

        # Adjust the timer intervals directly without stopping timers
        new_interval = int(100 / current_speed)  # Base interval is 100ms
        if self.timer_1.isActive():
            self.timer_1.setInterval(new_interval)
        if self.timer_2.isActive():
            self.timer_2.setInterval(new_interval)

        print(f"Speed adjusted to {current_speed}X, Timer Interval: {new_interval}ms")  # Debug

    def toggle_button_mode(self, button_key, active_text, inactive_text, buttons_to_hide, buttons_to_show):
        """
        Toggle the mode of a button and adjust the visibility of related buttons.
        Args:
            button_key: Key of the main button in the self.buttons dictionary.
            active_text: Text to display when the button is active.
            inactive_text: Text to display when the button is inactive.
            buttons_to_hide: List of button keys to hide when the main button is active.
            buttons_to_show: List of button keys to show when the main button is active.
        """
        main_button = self.buttons[button_key]
        is_active = main_button.text() == inactive_text

        if is_active:
            main_button.setText(active_text)
            self.hide_buttons(buttons_to_hide + ['play_pause_button_1', 'play_pause_button_2'])
            self.show_buttons(buttons_to_show)
        else:
            main_button.setText(inactive_text)
            self.hide_buttons(buttons_to_show)
            self.show_buttons(buttons_to_hide)

    def show_buttons(self, button_keys):
        """
        Show a list of buttons.
        Args:
            button_keys: List of button keys in the self.buttons dictionary to show.
        """
        for key in button_keys:
            if key in self.buttons:
                self.buttons[key].show()

    def hide_buttons(self, button_keys):
        """
        Hide a list of buttons.
        Args:
            button_keys: List of button keys in the self.buttons dictionary to hide.
        """
        for key in button_keys:
            if key in self.buttons:
                self.buttons[key].hide()

    def restore_buttons(self):
        """Restore all the buttons after adding a signal or canceling."""
        # Show the main buttons again

        self.buttons['unified_play_pause_button'].show()
        self.buttons['reset_button'].show()
        self.buttons['link_button'].show()
        self.buttons['add_signal_button'].setText("Add Signal")
        self.buttons['add_signal_button'].show()
        self.buttons['merge_button'].show()
        self.buttons['glue_button'].show()
        self.buttons['speed_button'].show()
        self.buttons['change_dynamic_signal'].show()

        # Hide the temporary buttons for graph selection
        self.buttons['add_signal_graph01'].hide()
        self.buttons['add_signal_graph02'].hide()

        print("Buttons restored. Ready for further actions.")

    def configure_plot(self, plot_widget, title):
        """Helper function to configure the plot widget."""
        plot_widget.setTitle(title, color="w", size="12pt")
        plot_widget.setLabel("left", "Amplitude (µV)", color="w", size="10pt")
        plot_widget.setLabel("bottom", "Time (s)", color="w", size="10pt")
        plot_widget.showGrid(x=True, y=True, alpha=0.3)

    def setup_buttons(self, layout, *buttons):
        """
        Set up the buttons with standard size, font, and style for consistent UI.
        """
        for button in buttons:
            button.setFixedSize(150, 40)  # Set a standard size for buttons
            button.setFont(QtGui.QFont("Times New Roman", 17))  # Apply font settings
            button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            button.setStyleSheet("""
                QPushButton {
                    border: 2px solid rgb(255, 255, 255);
                    background-color: rgb(36, 36, 36);
                    color: white;
                }
                QPushButton:hover {
                    background-color: rgb(50, 50, 50);
                }
            """)
            layout.addWidget(button)  # Add the button to the layout

    def hide_buttons(self, button_keys):
        """Hide a list of buttons specified by their keys in the self.buttons dictionary."""
        for key in button_keys:
            self.buttons[key].hide()

    def show_buttons(self, button_keys):
        """Show a list of buttons specified by their keys in the self.buttons dictionary."""
        for key in button_keys:
            self.buttons[key].show()

    '''---------------------------------------------------------------------------------------------------------------------------------------'''

    def initialize_RTS_graph(self, content_widget, signal_1_button,
                             get_rectangular_report_button, signal_1_label="Signals"):
        # Set up the canvas for plotting signals
        self.figure = Figure(figsize=(8, 6), dpi=100, facecolor='black', edgecolor='blue', frameon=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: black;")  # Set the canvas background to black

        content_widget.setGeometry(0, 80, 1280, 720)
        content_widget.setFixedHeight(720)
        # Create a vertical layout for the content and add the canvas
        layout = QtWidgets.QHBoxLayout(content_widget)
        layout.addWidget(self.canvas)

        # Create a horizontal layout for buttons
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing(30)  # Adjust spacing between buttons

        # Set up the font
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(17)

        # Add Play/Pause buttons for both signals
        signal_1_button.setFixedSize(150, 40)
        signal_1_button.setFont(font)  # Set Times New Roman font
        signal_1_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        signal_1_button.setStyleSheet("""
                QPushButton {
                    border: 2px solid rgb(255, 255, 255);
                    background-color: rgb(36, 36, 36);
                    color: white;
                }
                QPushButton:hover {
                    background-color: rgb(50, 50, 50);
                }
            """)
        signal_1_button.clicked.connect(
            lambda: self.toggle_play_pause_RTS_signal(self.timer_1, signal_1_button))
        button_layout.addWidget(signal_1_button)

        # Store play/pause buttons for later use in other methods
        self.play_pause_button_1 = signal_1_button

        '''# Add Replace Signal button
        get_rectangular_report_button.setFixedSize(150, 40)
        get_rectangular_report_button.setFont(font)  # Set Times New Roman font
        get_rectangular_report_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        get_rectangular_report_button.setStyleSheet("background-color: rgb(36,36,36); color: white;")
        get_rectangular_report_button.clicked.connect(self.open_reprot_page)
        button_layout.addWidget(get_rectangular_report_button)'''

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

        # Add back button using the add_back_button function
        back_button = self.add_back_button(content_widget)
        back_button.setFont(font)  # Set Times New Roman font
        back_button.clicked.connect(self.handle_back_button)
        button_layout.addWidget(back_button)

    def setup_RTS_page(self):
        if not hasattr(self, 'rts_initialized') or not self.rts_initialized:
            print("Setting up RTS page...")  # Debug

            # Create buttons for the RTS page
            play_pause_button_1 = QtWidgets.QPushButton("Play ▶", self.RTS_content)
            get_rectangular_report_button = QtWidgets.QPushButton("Get Report", self.RTS_content)

            # Call initialize_rectangular_graph with Rectangular-specific buttons and content
            self.initialize_RTS_graph(
                content_widget=self.RTS_content,
                signal_1_button=play_pause_button_1,
                get_rectangular_report_button=get_rectangular_report_button
            )

            self.timer_1 = QtCore.QTimer()

            self.timer_1.timeout.connect(
                lambda: self.update_RTS_signal('signal_data_1', 'Time_data_1', 'index_1', self.window_size_1, self.line_plot_1, self.ax1,
                                               self.timer_1))

            # Create the subplots for Rectangular (Signal 1) and ECG (Signal 2)
            self.ax1 = self.figure.add_subplot(111)
            self.ax1.set_facecolor('black')  # Set the plot background to black

            # Instantiate MplZoomHelper for the axis

            # Load and initialize Rectangular signal data
            filename = 'Data/RTS Data/RTS_data.txt'
            filename02 = 'Data/RTS Data/Time_data.txt'
            self.Time_data_1 = np.loadtxt(filename02)
            self.signal_data_1 = np.loadtxt(filename)
            self.index_1 = 0
            with open('Data/RTS Data/RTS_data.txt', 'r') as file:
                sum = 0
                for line in file:
                    sum += 1
            self.window_size_1 = sum
            self.line_plot_1, = self.ax1.plot(self.Time_data_1[:self.window_size_1],
                                              self.signal_data_1[:self.window_size_1], color=self.plot_color)
            self.ax1.tick_params(colors=self.label_color)

            self.ax1.minorticks_on()  # Enable minor ticks
            self.ax1.grid(True, which='minor', color='white', linestyle=':', linewidth=0.5, alpha=0.5)
            self.ax1.set_facecolor(self.backface_color)
            self.ax1.set_title("Signal")
            self.ax1.set_xlabel("Time")
            self.ax1.set_ylabel("Y(t)")

            self.setup_mouse_events()

            # Draw the canvas after initial setup
            self.canvas.draw()

            # Mark RTS page as initialized
            self.rts_initialized = True
            # Install event filter for scrolling

    def update_RTS_signal(self, signal_data_attr, Time_data_attr, index_attr, window_size, line_plot, ax, timer):
        self.update_RTS_data()  # Fetch new data
        # Reload the signal data from the file to ensure we have the latest data
        signal_data = np.loadtxt('Data/RTS Data/RTS_data.txt')
        setattr(self, signal_data_attr, signal_data)  # Update the attribute with new data

        Time_data = np.loadtxt('Data/RTS Data/Time_data.txt')
        setattr(self, Time_data_attr, Time_data)  # Update the attribute with new data

        index = getattr(self, index_attr)

        signal_data = getattr(self, signal_data_attr)
        Time_data = getattr(self, Time_data_attr)
        index = getattr(self, index_attr)

        if signal_data is not None and Time_data is not None:
            # Ensure we do not exceed the length of the signal data
            if index + window_size >= len(signal_data):
                timer.stop()  # Stop if we reach the end
                return

            # Prepare the x and y data
            x_data = Time_data[index:index + window_size]
            y_data = signal_data[index:index + window_size]

            # Check lengths
            if len(x_data) != len(y_data):
                print(f"Length mismatch: x_data={len(x_data)}, y_data={len(y_data)}")
                return

            # Update the plot
            line_plot.set_xdata(x_data)
            line_plot.set_ydata(y_data)

            ax.relim()
            ax.autoscale_view()

            # Redraw only the updated line
            self.canvas.draw_idle()

            # Update the index attribute
            setattr(self, index_attr, index + 1)  # Increment index

    def update_RTS_plot(self, val):
        start = int(self.start_slider.val)
        end = int(self.end_slider.val)

        # Update the plot based on slider values
        if end > start and end <= self.window_size_1:
            self.line_plot_1.set_xdata(np.arange(start, end))
            self.line_plot_1.set_ydata(self.signal_data_1[start:end])

            self.ax1.relim()
            self.ax1.autoscale_view()
            self.canvas.draw_idle()

    def get_real_time_data(self):
        """Fetch real-time data from the Weather API and return current time and temperature."""
        url = "https://api.weatherapi.com/v1/current.json?key=135b4139f4fc40a48ba202601240910&q=egypt&aqi=no"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()
            temp_c = data['current']['temp_c']
            localtime_epoch = (data['location']['localtime_epoch'] // 60) % 10000
            return temp_c, localtime_epoch
        except requests.exceptions.RequestException as e:
            print("Error fetching data:", e)
            return None

    def update_RTS_data(self):
        """Fetch and update RTS signal data."""
        temp_c, localtime_epoch = self.get_real_time_data()

        if temp_c is not None:  # Ensure we have valid temperature data
            temp = self.fix_decimal_format(str(temp_c))
            with open('Data/RTS Data/RTS_data.txt', 'a') as file:
                file.write(str(temp) + '\n')
        else:
            print("Failed to update RTS signal.")
        if localtime_epoch is not None:  # Ensure we have valid temperature data
            with open('Data/RTS Data/Time_data.txt', 'a') as file:
                file.write(str(localtime_epoch) + '\n')
        else:
            print("Failed to update RTS signal.")

    def fix_decimal_format(self, number_str):
        # Split the number string by the decimal point
        parts = number_str.split('.')

        # If there are more than two parts, combine the first two parts with a single decimal point
        if len(parts) > 2:
            number_str = parts[0] + '.' + ''.join(parts[1:])

        return number_str

    def toggle_play_pause_RTS_signal(self, timer, button):
        """Toggle between playing and pausing a signal."""
        # Handle individual signals
        if button.text() == "Play ▶":
            self.play_RTS_signal(timer)
            button.setText("Pause")
        else:
            self.pause_RTS_signal(timer)
            button.setText("Play ▶")

    def play_RTS_signal(self, timer):
        """Start the timer to play the signal animation."""
        timer.start(180000)  # Update every 3 minutes

    def pause_RTS_signal(self, timer):
        """Stop the timer to pause the signal animation."""
        timer.stop()

    def on_click(self, event, ax, canvas, signal_data):
        setattr(self, 'start', 1)
        setattr(self, 'end', self.window_size_1)

        if event.button == 1:  # Left-click (Zoom In)
            self.factor += 0.2
            self.start *= self.factor
            self.end *= self.factor

            self.start = max(0, min(int(self.start), len(signal_data) - 1))
            self.end = max(0, min(int(self.end), len(signal_data)))

            x_data = np.arange(int(self.start), int(self.end))
            y_data = signal_data[int(self.start):int(self.end)]

            if len(x_data) != len(y_data):
                print(f"Shape mismatch: x_data length = {len(x_data)}, y_data length = {len(y_data)}")
                return

            ax.lines[0].set_xdata(x_data)
            ax.lines[0].set_ydata(y_data)
            ax.relim()
            ax.autoscale_view()
            canvas.draw_idle()

        elif event.button == 3:  # Right-click (Zoom Out)
            self.factor -= 0.2
            self.start *= self.factor
            self.end *= self.factor

            x_data = np.arange(int(self.start), int(self.end))
            y_data = signal_data[int(self.start):int(self.end)]

            if len(x_data) != len(y_data):
                print(f"Shape mismatch: x_data length = {len(x_data)}, y_data length = {len(y_data)}")
                return

            ax.lines[0].set_xdata(x_data)
            ax.lines[0].set_ydata(y_data)
            ax.relim()
            ax.autoscale_view()
            canvas.draw_idle()

    def setup_mouse_events(self):
        """Setup mouse events for both canvases."""
        if hasattr(self, 'canvas_1') and hasattr(self, 'canvas_2'):
            # Setup mouse events for ax1 (canvas_1)
            self.canvas_1.mpl_connect('button_press_event',
                                      lambda event: self.on_click(event, self.ax1, self.canvas_1,
                                                                  self.signals_data_ax1))

            # Setup mouse events for ax2 (canvas_2)
            self.canvas_2.mpl_connect('button_press_event',
                                      lambda event: self.on_click(event, self.ax2, self.canvas_2,
                                                                  self.signals_data_ax2))

    '''----------------------------------------------------------------------------------------------------------------------------'''

    def setup_circular_page(self):
        if not hasattr(self, 'circular_initialized') or not self.circular_initialized:
            print("Setting up Circular page...")

            # Set the background color of the widget to black
            self.circular_content.setStyleSheet("background-color: black;")

            # Create buttons for the Circular page
            circular_play_button = QtWidgets.QPushButton("Play ▶", self.circular_content)
            replace_signal_button = QtWidgets.QPushButton("Replace Signal", self.circular_content)
            set_color_button = QtWidgets.QPushButton("Set Color", self.circular_content)

            self.figure = Figure(figsize=(8, 6), dpi=100, facecolor='black')
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background-color: black;")  # Set the canvas background to black

            # Create layouts for the content and buttons
            layout = QtWidgets.QHBoxLayout(self.circular_content)
            layout.addWidget(self.canvas)
            circular_button_layout = QtWidgets.QVBoxLayout()

            font = QtGui.QFont("Times New Roman", 17)

            for button in [circular_play_button, replace_signal_button, set_color_button]:
                button.setFont(font)
                button.setFixedSize(150, 40)
                button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                button.setStyleSheet("""
                QPushButton {
                    border: 2px solid rgb(255, 255, 255);
                    background-color: rgb(36, 36, 36);
                    color: white;
                }
                QPushButton:hover {
                    background-color: rgb(50, 50, 50);
                }
            """)
                circular_button_layout.addWidget(button)

            circular_play_button.clicked.connect(lambda: self.toggle_play_pause_circular_signal(circular_play_button))
            replace_signal_button.clicked.connect(self.replace_circular_signal)
            set_color_button.clicked.connect(self.open_color_picker)

            layout.addLayout(circular_button_layout)

            # Load data and set up the plot
            self.load_circular_data()
            self.ax_polar = self.figure.add_subplot(111, projection='polar')
            self.ax_polar.set_facecolor('black')  # Set the plot background to black
            self.line_polar, = self.ax_polar.plot([], [], lw=2, color='white')  # Set default line color to white for visibility
            self.ax_polar.tick_params(axis='x', colors='white')  # Change the color of the tick marks to white
            self.ax_polar.tick_params(axis='y', colors='white')
            self.canvas.draw()
            self.circular_initialized = True

    def toggle_play_pause_circular_signal(self, button):
        if button.text() == "Play ▶":
            button.setText("Pause")
            if not hasattr(self, 'ani_polar'):
                from matplotlib.animation import FuncAnimation

                def update_polar(frame):
                    angles = np.linspace(0, 2 * np.pi, len(self.data) + 1)
                    radii = np.append(self.data, self.data[0])[:frame + 1]
                    self.line_polar.set_data(angles[:frame + 1], radii)
                    return self.line_polar,

                def on_animation_complete(animation, *args):
                    button.setText("Play ▶")
                    animation.event_source.stop()  # Stop the animation event source when animation completes

                # Lower the interval for faster animation, e.g., from 100ms to 10ms
                self.ani_polar = FuncAnimation(self.figure, update_polar, frames=len(self.data) + 1, blit=True, interval=5, repeat=False)
                self.ani_polar.event_source.start()
                # Connect the animation completion callback
                self.ani_polar._on_finish = lambda: on_animation_complete(self.ani_polar)
            else:
                self.ani_polar.event_source.start()
        else:
            button.setText("Play ▶")
            if hasattr(self, 'ani_polar'):
                self.ani_polar.event_source.stop()

    def load_circular_data(self):
        file_path = '/Users/yassientawfik/Desktop/normal_ecg.csv'
        try:
            self.data = np.loadtxt(file_path, delimiter=',')
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            self.data = np.linspace(1, 100, 100)  # Default data if file not found
            print("Loaded default circular data")

    def replace_circular_signal(self):
        if hasattr(self, 'circular_initialized') and self.circular_initialized:
            self.load_circular_file(self.load_circular_data_from_file)
        else:
            print("Circular page not initialized or circular data not found")

    def load_circular_data_from_file(self, file_path):
        """Load circular data from the specified single-column CSV file path."""
        try:
            self.data = np.loadtxt(file_path, delimiter=',')
            print("Data loaded successfully. Updating plot...")
            self.update_circular_plot()
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            if hasattr(self, 'show_error_message'):
                self.show_error_message(f"Error loading file: {e}")

    def update_circular_plot(self):
        print("Update Circular Plot called")
        if hasattr(self, 'ax_polar') and hasattr(self, 'data'):
            # Clear the existing plot
            self.figure.clear()
            # Re-create the polar subplot
            self.ax_polar = self.figure.add_subplot(111, projection='polar')

            # Check if we have enough data to plot
            if len(self.data) > 1:
                # Create angles array to match data length, include endpoint to close the circle
                angles = np.linspace(0, 2 * np.pi, len(self.data) + 1)

                # Append the first data point to the end to close the circle
                complete_data = np.append(self.data, self.data[0])

                # Plot the data
                self.line_polar, = self.ax_polar.plot(angles, complete_data, lw=2)

                # Optionally set the direction of the zero angle and location of 0 degrees
                self.ax_polar.set_theta_zero_location('N')  # 'N' for North
                self.ax_polar.set_theta_direction(-1)  # Clockwise

            else:
                print("Not enough data to create a polar plot.")

            # Redraw the plot
            self.canvas.draw_idle()
        else:
            print("Circular plot or data not available")

    def load_circular_file(self, load_signal_data_callback):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Load Signal File",
                                                             "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_path:
            load_signal_data_callback(file_path)

    def open_color_picker(self):
        color_dialog = ColorPickerDialog(self)
        color_dialog.exec_()

    '''---------------------------------------------------------------------------------------------------------------------------------------'''

    def initialize_ax(self, ax, title, xlabel, ylabel, signals_data, line_plots, selector_callback=None):
        """Initialize axes with properties, grid, and plots."""
        ax.set_facecolor(self.backface_color)
        ax.minorticks_on()
        ax.grid(True, which='minor', color='lightgray', linestyle=':', linewidth=0.5, alpha=0.5)
        ax.set_title(title, color=self.label_color)
        ax.set_xlabel(xlabel, color=self.label_color)
        ax.set_ylabel(ylabel, color=self.label_color)
        ax.tick_params(colors=self.label_color)

        # Set limits if signals_data exist
        if signals_data:
            ax.set_xlim(0, self.window_size_1)
            ax.set_ylim(min(np.min(sig) for sig in signals_data),
                        max(np.max(sig) for sig in signals_data))

        # Initialize line plots
        for signal_data in signals_data:
            line_plot, = ax.plot([], [], color=self.plot_color)
            line_plots.append(line_plot)

        # Add RectangleSelector if callback is provided
        if selector_callback:
            selector = RectangleSelector(
                ax, onselect=selector_callback, useblit=True,
                button=[1], minspanx=5, minspany=5,
                spancoords='pixels', interactive=True
            )
            return selector
        return None


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    global_saved_snapshots = []
    global_saved_statistics = []
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.showFullScreen()
    sys.exit(app.exec_())
