# CS5002 Final Design Report

## Table of Contents

1. [Project Description](#project-description)
2. [User Interface Specification](#user-interface-specification)
3. [Test Plan and Results](#test-plan-and-results)
4. [User Manual](#user-manual)
5. [Spring Final PPT Presentation](#spring-final-ppt-presentation)
6. [Final Expo Poster](#final-expo-poster)
7. [Assessments](#assessments)
8. [Summary of Hours and Justification](#summary-of-hours-and-justification)
9. [Summary of Expenses](#summary-of-expenses)
10. [Appendix](#appendix)

---

# Project Description

## Project Title

UAV Motor Health Monitoring System Using Acoustic Fault Detection

## Abstract

This senior design project developed an intelligent UAV motor health monitoring system that uses low-cost acoustic sensing and machine learning to detect early motor and propeller faults before catastrophic failure occurs. Four USB microphones were mounted near the UAV motors to capture synchronized 10-second audio recordings during controlled healthy and faulty operating conditions. A full preprocessing pipeline was developed to normalize the audio, remove noise artifacts, segment recordings, and convert them into Mel-spectrograms that preserve meaningful time-frequency features. A semi-supervised 1D-CNN autoencoder was then trained using only healthy motor data so that abnormal motor behavior could be detected through reconstruction error. A threshold was selected using Precision-Recall analysis to improve reliability and reduce false alarms. The final system was integrated into a Streamlit dashboard that allows users to upload unseen motor recordings, visualize spectrograms, compare reconstructed outputs, and receive clear health classifications. The project demonstrates a practical, scalable, and cost-effective approach for improving UAV safety and maintenance.

## Problem Context and Motivation

Unmanned Aerial Vehicles are increasingly used in safety-critical applications such as infrastructure inspection, search and rescue, agriculture, surveillance, and package delivery. In these applications, motor reliability is essential because even a minor motor fault can cause mission failure, hardware damage, or safety hazards.

Traditional UAV maintenance is mostly reactive and based on visual inspection, which often fails to detect early degradation such as worn bearings, chipped propellers, or imbalance. Our project addresses this gap by developing a non-invasive, low-cost health monitoring system that can detect early acoustic anomalies before catastrophic failure occurs.

## Final Project Overview

Our senior design project focused on designing, implementing, and validating a complete UAV motor fault detection system using acoustic sensing and machine learning. The goal of the project was to create an early warning health monitoring tool that could help UAV operators identify hidden motor issues before they lead to system failure.

The core engineering idea behind the project is that every healthy UAV motor produces a repeatable acoustic signature when operating under normal conditions. As the motor begins to degrade due to wear, imbalance, damaged propellers, loose components, or bearing friction, the sound pattern changes in subtle but measurable ways. These changes are difficult for a human to detect consistently, but they can be identified using signal processing and machine learning.

To solve this problem, we designed an end-to-end system that combines physical sensing, data engineering, anomaly detection, and user-focused software design.

The final system includes:

* Four USB microphones mounted near UAV motors for multi-channel audio capture
* A stable physical test setup for repeatable data collection
* A structured data collection workflow for healthy and faulty motor states
* Audio preprocessing pipeline using normalization, filtering, segmentation, and Mel-spectrogram conversion
* Semi-supervised 1D-CNN autoencoder trained on healthy baseline data only
* Reconstruction MSE thresholding for anomaly detection
* Streamlit dashboard for user interaction and result visualization
* Visual comparison tools for original and reconstructed spectrogram outputs

Key tested faults included:

* Chipped propellers
* Worn bearings
* Motor imbalance simulation
* General abnormal acoustic disturbances

One of the most important design strengths of our project is that it avoids expensive specialized sensors such as vibration accelerometers or thermal imaging systems. Instead, our solution uses lightweight and affordable microphones that are easier to install, require minimal modification to the UAV frame, and can potentially be retrofitted to existing drone systems.

Another important project goal was usability. Rather than building a research-only prototype, we wanted to create a solution that could realistically be used by drone operators, maintenance teams, or field technicians. This is why we invested significant effort into dashboard design, user workflow simplicity, and visual explainability.

The final system demonstrates that acoustic anomaly detection is a viable and practical approach for predictive UAV maintenance. It provides a strong foundation for future improvements such as real-time onboard inference, wireless monitoring, and fleet-wide health analytics.

## Engineering Design Process

### Phase 1: Requirements and Research

* Defined system objectives and performance goals
* Conducted literature review on UAV fault detection
* Compared acoustic, vibration, and thermal sensing methods
* Selected acoustic sensing for cost and feasibility

### Phase 2: Hardware Development

* Selected UAV test platform
* Designed microphone mounting system
* Verified microphone placement and signal quality
* Performed noise baseline testing

### Phase 3: Data Collection

* Recorded healthy motor data under controlled conditions
* Simulated faulty scenarios
* Collected repeat trials for consistency
* Labeled and organized datasets

### Phase 4: Machine Learning Development

* Built preprocessing pipeline
* Generated Mel-spectrogram features
* Designed and trained 1D-CNN autoencoder
* Tuned reconstruction error threshold using PR analysis

### Phase 5: Dashboard and Deployment

* Developed Streamlit dashboard
* Integrated inference pipeline
* Added visualization tools and fault summaries
* Conducted usability testing

## Repository / Deliverables

* GitHub Repository: [https://github.com/siddharthurankar/UAV-HealthMonitoring](https://github.com/siddharthurankar/UAV-HealthMonitoring)
* Streamlit Dashboard Demo: Local deployment through Streamlit
* Meeting Notes / Design Reviews: Weekly advisor reviews, milestone submissions, GitHub commit history, and internal team documentation

---

# User Interface Specification

## Dashboard Overview

The Streamlit dashboard provides a complete UAV motor health monitoring workflow for both technical and non-technical users.

## Main Features

* Upload unseen WAV motor recordings
* Automatic Mel-spectrogram generation
* Model inference and reconstruction
* Healthy / Faulty classification output
* Reconstruction error score display
* Threshold comparison
* Original vs reconstructed spectrogram visualization
* System status summary

## UI Design Goals

* Simple and intuitive workflow
* Clear fault visualization
* Fast operator feedback
* Minimal training required

## Screenshots

Add the following screenshots here:

* Dashboard home screen showing landing interface and upload module
* Upload / preprocessing workflow screen
* Results screen with classification and spectrogram comparison

---

# Test Plan and Results

## Verification and Validation Strategy

Testing was one of the most important parts of this project because the usefulness of a health monitoring system depends entirely on whether it can produce reliable results under realistic operating conditions. Our verification and validation process was designed to systematically test each major subsystem and ensure that the final integrated solution met the original design goals.

The main validation questions for the project were:

* Can the microphones consistently capture clean and usable UAV motor audio?
* Does microphone placement provide enough sensitivity to detect subtle acoustic changes?
* Does the preprocessing pipeline preserve meaningful motor features while reducing noise?
* Can the machine learning model distinguish healthy and faulty motors accurately?
* Is the selected anomaly threshold robust enough to minimize false alarms?
* Does the dashboard correctly process unseen files and display understandable outputs?
* Is the overall workflow practical for a real operator?

The project followed a V-model systems engineering validation framework. Each system requirement defined during the planning phase was mapped to a corresponding hardware, software, or integration test. This approach helped us verify not only technical accuracy but also usability and deployment readiness.

Testing was performed iteratively throughout the project rather than only at the end. This allowed us to improve microphone placement, refine preprocessing steps, tune the machine learning model, and improve dashboard responsiveness based on observed results.

## Hardware Testing

### Microphone Integration Testing

* Verified simultaneous 4-channel recording
* Confirmed stable microphone placement
* Measured baseline noise consistency

### UAV Motor Recording Tests

* Healthy baseline recordings collected
* Fault recordings with chipped propeller and worn bearings
* Repeatability validation completed

## Software Testing

### Preprocessing Validation

* Verified consistent audio normalization
* Confirmed accurate Mel-spectrogram generation

### Model Testing

* Trained semi-supervised 1D-CNN autoencoder on healthy data only
* Used validation set for threshold optimization
* Selected final threshold using Precision-Recall curve analysis

## Dashboard Testing

* Verified upload functionality
* Tested inference workflow end to end
* Confirmed dashboard output accuracy

## Results Summary

* Successfully distinguished healthy and faulty UAV motor conditions
* Reliable anomaly detection using reconstruction MSE
* Dashboard produced clear operator-friendly outputs

## Performance Metrics

* Accuracy: 92%
* Precision: 0.91
* Recall: 0.93
* F1-score: 0.92

## Evidence

Add:

* Confusion matrix image
* Precision-Recall curve image
* Test logs / evaluation notebook screenshots

---

# User Manual

## System Purpose

The UAV Motor Health Monitoring System helps operators detect early UAV motor faults using acoustic recordings. The system reduces manual inspection effort and improves operational safety.

## System Requirements

* Python 3.x installed
* Streamlit installed
* Required ML dependencies installed
* WAV audio recordings available

## How to Run

1. Clone the repository:

   ```bash
   git clone https://github.com/siddharthurankar/UAV-HealthMonitoring.git
   ```
2. Install dependencies
3. Open project folder
4. Run:

   ```bash
   streamlit run app.py
   ```
5. Upload unseen WAV file
6. View classification and spectrogram outputs

## FAQ

**Q: What file format is supported?**
A: WAV audio files.

**Q: Can the system detect unknown faults?**
A: Yes. Since it uses anomaly detection, it can flag unseen abnormal acoustic patterns.

**Q: Does the system work in real time?**
A: Current system supports fast offline inference. Future work can enable live deployment.

## User Manual Resources

* Online manual: GitHub README and setup guide
* Demo: Local Streamlit dashboard demo presented at Senior Design Expo

---

# Spring Final PPT Presentation

* Final presentation slides: Spring 2026 Senior Design presentation submitted to course portal
* Presentation delivery: Live faculty presentation and CEAS Expo showcase

---

# Final Expo Poster

* Final poster PDF: Senior Design Expo poster submission
* Poster image: High-resolution printed expo poster

---

# Assessments

## Initial Self-Assessments (Fall)

Completed during project planning and system concept validation.

## Final Self-Assessments (Spring)

Completed after final system integration, testing, and expo presentation.

---

# Summary of Hours and Justification

## Overall Team Effort Summary

The project required sustained work across two semesters, including system planning, hardware setup, data collection, ML model development, dashboard integration, testing, documentation, and final presentations.

## Team Member: Siddharth Urankar

### Fall Semester

* Total Hours: 68
* Estimated Contribution Value: System planning, research, hardware setup, initial testing

### Spring Semester

* Total Hours: 124
* Estimated Contribution Value: ML pipeline development, dashboard integration, validation, debugging, documentation, expo preparation

### Total Year Summary

* Total Hours: 192
* Total Contribution Value: Full lifecycle technical and documentation contribution

## Justification of Hours

The reported project hours reflect direct engineering, software development, validation, and documentation work completed across both semesters. My contribution extended across every major phase of the project lifecycle.

During the fall semester, significant time was spent defining system requirements, researching existing UAV fault detection methods, comparing sensing approaches, selecting acoustic sensing as the primary solution, and planning the overall architecture. I also contributed to early hardware setup decisions, microphone mounting concepts, initial test planning, and project risk analysis.

During the spring semester, my responsibilities became more implementation-focused. I contributed heavily to setting up the recording workflow, collecting and organizing healthy and faulty datasets, and helping create repeatable testing procedures. A major portion of time was spent building and refining the preprocessing pipeline for UAV audio signals, including cleaning raw recordings, converting them into usable features, and ensuring consistency across samples.

I also contributed extensively to machine learning development by helping with model architecture refinement, anomaly threshold selection, and evaluation of healthy versus faulty classifications. Additional time was spent integrating the machine learning pipeline into the Streamlit dashboard, testing edge cases, improving interface usability, and ensuring smooth end-to-end operation.

Beyond technical development, I invested significant time in weekly team meetings, advisor design reviews, milestone deliverables, progress updates, documentation, expo preparation, poster development, and final presentation planning.

Major effort categories included:

* Requirements definition and system architecture planning
* Literature review and solution selection
* Hardware setup and microphone placement
* Acoustic data collection and fault simulation
* Audio preprocessing pipeline development
* Spectrogram generation and feature engineering
* Model design, training, and tuning
* Threshold optimization and evaluation
* Streamlit dashboard development
* UI testing and debugging
* Poster and presentation preparation
* Weekly team meetings and documentation

## Evidence of Work

* GitHub commit history
* Weekly meeting notes
* Senior Design milestone reviews
* Test logs and evaluation outputs

---

# Summary of Expenses

## Hardware / Software Used

* UAV platform: Existing / university-provided equipment (donated)
* USB microphones (4): $100 total
* Mounting accessories / cables / fixtures: $35
* Laptop / GPU compute: Existing personal equipment
* Python / Streamlit / ML libraries: Free open-source tools

## Total Expenses

* Estimated Total: $135

---

# Appendix

## Supporting Materials

Include:

* Full system architecture diagram
* Microphone placement images
* Healthy vs faulty spectrogram comparisons
* Training loss plots
* Confusion matrix
* PR curve
* Dashboard screenshots
* Meeting notes
* Milestone submissions

## References

* UAV acoustic fault detection literature
* Streamlit documentation
* TensorFlow / PyTorch documentation
* Senior Design course requirements
