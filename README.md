# Dynamic Multi-Channel Signal Viewer

### **Overview**
The Dynamic Multi-Channel Signal Viewer is a Python and Qt-based desktop application for visualizing and managing medical signals such as ECG, EMG, and EEG. The application simulates ICU monitoring systems and offers a variety of features for signal playback, customization, and reporting.

---

### **Features**

1. **Signal Playback Controls (Rectangular Signal)**:
   - **Play/Pause**: Start or pause the playback of the signal.
   - **Speed**: Adjust the playback speed dynamically.
   - **Change Signal**: Switch the active signal being controlled in the playback.

2. **Graph Management**:
   - **Add Signal**: Add a static signal to the graph for comparison.
   - **Merge**: Overlay two signals on the same graph or separate them into individual graphs.
   - **Link/Unlink**: Synchronize or separate playback and zooming between two graphs.

3. **Signal Customization**:
   - **Change Colors**: Adjust the signal color for better visualization.
   - **Labels/Titles**: Add or edit labels and titles for the signals.

4. **Advanced Features**:
   - **Glue**: Open the **Glue Window** to combine parts of different signals. Ensure to press **Save Data** before using **Get Report** to generate a PDF report.

5. **Weather Indication (Real-Time Signal - RTS)**:
   - Displays a visual indication of the current weather conditions.

6. **Circular Signal**:
   - Upload and plot a circular signal for unique signal analysis.

---

### **Application Interface**
Below are screenshots of the application demonstrating its key features:

1. **Main Interface with Two Independent Graphs**  
   ![Main Interface](https://github.com/user-attachments/assets/2c6bc2bf-5924-4e73-aaf0-e1a3b51f33ba)

2. **Graph Linking and Signal Manipulation**  
   ![Graph Linking](https://github.com/user-attachments/assets/f8afb6e1-5fb5-4b46-b0bb-be5f1eb6881e)

3. **Glue Window with Save Data and Get Report Buttons**  
   Ensure to press the **Save Data** button before generating the report using the **Get Report** button.  
   ![Glue Window](https://github.com/user-attachments/assets/fdaed8a2-22a7-49a9-b5a9-c7657e8f59dd)

4. **Signal Playback and Navigation**  
   ![Signal Playback](https://github.com/user-attachments/assets/1ab3a206-43c6-476d-a454-d6587a470e0c)

5. **Circular Signal Visualization**  
   ![Circular Signal](https://github.com/user-attachments/assets/14a29bca-8649-40a0-846c-0d7f23d1ea7d)

---

### **Setup and Installation**
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/YassienTawfikk/Dynamic-Multi-Channel-Signal-Viewer.git
   ```
2. **Navigate to the Project Directory**:
   ```bash
   cd Dynamic-Multi-Channel-Signal-Viewer
   ```
3. **Install Required Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Application**:
   ```bash
   python Main.py
   ```

---

### **Usage Instructions**
1. Launch the application and browse your PC to load signal files.
2. Use the playback controls to pause, rewind, or change playback speed.
3. Customize signals by changing colors, labels, or zoom/pan controls.
4. Link or unlink graphs for synchronized viewing.
5. In the **Glue Window**, press **Save Data** before using **Get Report** to generate a complete PDF report.

---

### **Shout out to the team**

- [Yassien Tawfik](https://github.com/YassienTawfikk)
- [Nancy Mahmoud](https://github.com/nancymahmoud1)
- [Madonna Mosaad](https://github.com/madonna-mosaad)
---

### **Contact**
For any inquiries or feedback, please contact:
- **Name**: Yassien Tawfik
- **Email**: Yassien.m.m.tawfik@gmail.com
