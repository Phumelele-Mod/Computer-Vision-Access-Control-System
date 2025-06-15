# Computer Vision-Based Access Control System

This repository contains the implementation of a **computer vision-based access control system** designed for secure, contactless authentication in residential environments. The system integrates **facial recognition** and **QR code scanning** for user authentication, a **Flask-based web application** for administrative control, mongodb atlas database for storing user information access logs and admin credentials.

It was developed, in 2025, as a final-year project for the **Bachelor of Engineering in Electrical and Electronics Engineering** at the **University of Eswatini**.

---

## Overview

The system achieves:

- **87.1%** accuracy for facial recognition using DeepFace and MTCNN  
- **99.9%** accuracy for QR code authentication with PyZBar and AES-128 encryption (Fernet)  
- **134.8 ms** average QR code processing time and **1840 ms** facial recognition 
- Secure cloud storage with **MongoDB Atlas** and a user-friendly web interface  

---

## System Architecture

The system comprises **three main components**:

- **Raspberry Pi Module**  
  Handles:
  - Facial recognition (DeepFace, MTCNN)
  - QR code scanning (PyZBar, Fernet)
  - Gate control (via GPIO pins and a one-channel relay to a gate controller)

- **Web Application**  
  A Flask-based admin interface for:
  - User management
  - Authentication logs
  - Remote gate control
  - Viewing live feed 
  Connected to MongoDB Atlas for data storage

- **Database**  
  Stores:
  - Permanent users  
  - Temporal users  
  - Admin credentials  
  - Access logs  

---

## Hardware Requirements

- Raspberry Pi 4 Model B (8GB RAM)  
- Raspberry Pi HQ Camera 12.3 MP  
- MicroSD card at least 32 GB
- 5V/3A USB-C power supply  
- One-channel relay (5V DC, 10A AC)    
- Weatherproof plastic enclosure  

---

## Software Requirements

- Raspberry Pi OS (64-bit)  
- Python 3.9 or higher  
- MongoDB Atlas account  
- Python libraries (see `Pi_Code/requirements.txt` and `Access Control App-Copy/requirements.txt`):  
  - `deepface`, `mtcnn`, `pyzbar`, `cryptography`, `flask`, `pymongo`, `opencv-python`, `rpi.gpio`

---

## Installation

### Raspberry Pi Setup

1. Flash Raspberry Pi OS to the microSD card using **Raspberry Pi Imager**  
2. Boot the Raspberry Pi and update the system:
    ```bash
    sudo apt update && sudo apt upgrade
    ```
3. Install Python dependencies:
    ```bash
    cd pi_code
    pip install -r requirements.txt
    ```
4. Configure environment variables in `pi_code/.env`:
    ```env
    CAMERA_DEVICE=/dev/video0
    GPIO_RELAY_PIN=18
    ```

### Web App Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/Phumelele-Mod/Computer-Vision-Based-Access-Control-System.git
    ```
2. Configure environment variables
2. Install dependencies:
    ```bash
    cd Access Control App-Copy
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
5. Access the web app at [http://<ip_address>:<port_no>](http://<ip_address>:<port_no>)

---

## Usage

### Raspberry Pi Module

1. Run the raspberry pi script:
    ```bash
    cd pi_code
    python pi_code.py
    ```
2. Upon successful authentication (face or QR or admin control), the system triggers the **Gate** via the relay.

### Web Application

1. Open a browser and go to: [http://<ip_address>:<port_no>](http://localhost:5000)  
2. Log in to the admin interface to:
   - Add or remove users 
   - View authentication logs
   - View live feed
   - Control gate remotely
   - Change password

---

## Performance Results

- **Facial Recognition**  
  - 87.1% accuracy
  - Average processing time: 1840 ms
  - Tested with 15 users registered users and 10 imposters under good lighting conditions

- **QR Code Authentication**  
  - 99.9% accuracy  
  - Average processing time: 134.8 ms
  - Tested with 10 valid QR codes and 5 invalid codes 

- **Gate Integration**  
  - Successfully integrated with a **Centurion D5-Evo gate controller**  

---


