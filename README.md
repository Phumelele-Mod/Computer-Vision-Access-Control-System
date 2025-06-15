# Computer Vision-Based Access Control System

This repository contains the implementation of a **computer vision-based access control system** designed for secure, contactless authentication in residential environments. The system integrates **facial recognition** and **QR code scanning** for user authentication, a **Flask-based web application** for administrative control, and hardware integration with a **D5-Evo gate controller**.

It was developed as a final-year project for the **Bachelor of Engineering in Electrical and Electronics Engineering** at the **University of Eswatini**.

---

## 📋 Overview

The system achieves:

- **87.1%** accuracy for facial recognition using DeepFace and MTCNN  
- **99.9%** accuracy for QR code authentication with PyZBar and AES-128 encryption (Fernet)  
- **134.8 ms** average QR code processing time and **120 ms** gate response  
- Secure cloud storage with **MongoDB Atlas** and a user-friendly web interface  

---

## 🧠 System Architecture

The system comprises **three main components**:

- **Raspberry Pi Module**  
  Handles:
  - Facial recognition (DeepFace, MTCNN)
  - QR code scanning (PyZBar, Fernet)
  - Gate control (via GPIO pins and a one-channel relay to the D5-Evo gate controller)

- **Web Application**  
  A Flask-based admin interface for:
  - User management
  - Authentication logs
  - System monitoring  
  Connected to MongoDB Atlas for data storage

- **Database**  
  Stores:
  - Permanent users  
  - Temporal users  
  - Admin credentials  
  - Access logs  

---

## 🔌 Hardware Requirements

- Raspberry Pi 4 Model B (8GB RAM)  
- Raspberry Pi HQ Camera with M12 high-resolution lens  
- 64GB microSD card  
- 5V/3A USB-C power supply  
- One-channel relay (5V DC, 10A AC)  
- D5-Evo gate controller  
- Weatherproof plastic enclosure  

---

## 💻 Software Requirements

- Raspberry Pi OS (64-bit)  
- Python 3.9 or higher  
- MongoDB Atlas account  
- Python libraries (see `pi_code/requirements.txt` and `web_app/requirements.txt`):  
  - `deepface`, `mtcnn`, `pyzbar`, `cryptography`, `flask`, `pymongo`, `opencv-python`, `rpi.gpio`

---

## ⚙️ Installation

### 🖥 Raspberry Pi Setup

1. Flash Raspberry Pi OS to the microSD card using **Raspberry Pi Imager**  
2. Connect the camera, relay, and power supply as shown in `images/hardware_setup.jpg`  
3. Boot the Raspberry Pi and update the system:
    ```bash
    sudo apt update && sudo apt upgrade
    ```
4. Install Python dependencies:
    ```bash
    cd pi_code
    pip install -r requirements.txt
    ```
5. Configure environment variables in `pi_code/.env`:
    ```env
    CAMERA_DEVICE=/dev/video0
    GPIO_RELAY_PIN=23
    ```

### 🌐 Web App Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/Access-Control-System-RPi.git
    ```
2. Install dependencies:
    ```bash
    cd web_app
    pip install -r requirements.txt
    ```
3. Create a MongoDB Atlas account at [mongodb.com](https://mongodb.com), set up a cluster, and add your connection string in `web_app/.env`:
    ```env
    MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.mongodb.net/
    FLASK_SECRET_KEY=your-secret-key
    ```
4. Run the Flask app:
    ```bash
    python app.py
    ```
5. Access the web app at [http://localhost:5000](http://localhost:5000)

> 📄 See `docs/setup_guide.md` for detailed instructions.

---

## 🚀 Usage

### 🎥 Raspberry Pi Module

1. Run the facial recognition and QR code scanning scripts:
    ```bash
    cd pi_code
    python facial_recognition.py
    python qr_code_scanner.py
    ```
2. Upon successful authentication (face or QR), the system triggers the **D5-Evo gate** via the relay.

### 🧑‍💼 Web Application

1. Open a browser and go to: [http://localhost:5000](http://localhost:5000)  
2. Log in to the admin interface to:
   - Add or remove users (upload face images and generate QR codes)
   - View authentication logs
   - Monitor system status

---

## 📊 Performance Results

- **Facial Recognition**  
  - 87.1% accuracy  
  - Tested with 100 users under varied lighting conditions  

- **QR Code Authentication**  
  - 99.9% accuracy  
  - Average processing time: 134.8 ms  

- **Gate Integration**  
  - 100% success rate  
  - 120 ms response time for gate activation  

---

## 📁 Folder Structure (Simplified)


