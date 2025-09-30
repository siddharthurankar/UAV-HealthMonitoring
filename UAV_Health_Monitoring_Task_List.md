# UAV Health Monitoring Task List

## Ally Blair (ME) – Mechanical Systems, Data Collection

- Assemble UAV and test platform with stable mounting for motors and sensors.  
- Conduct vibration isolation experiments to reduce structural noise in audio recordings.  
- Compare microphone types (MEMS vs USB) under identical test conditions.  
- Determine optimal microphone placement through controlled bench testing.  
- Induce controlled propeller faults (e.g., chipped, unbalanced, bent blades) for dataset generation.  
- Induce controlled motor faults (e.g., bearing wear, partial short) and record signatures.  
- Establish safety protocols for running UAVs with faulty motors during testing.  
- Record baseline healthy motor datasets across different operating conditions (RPM, load, environment).  
- Record faulty motor datasets at varying fault severity levels for training/evaluation.  
- Document mechanical test setup including fault induction procedures, mic placement diagrams, and UAV configuration.  

## Prissha Chawla (CS) – Data Science, AI, ML

- Design of experiment plan detailing recording scenarios, environmental variations, and repetitions.  
- Perform exploratory data analysis (EDA) on collected motor audio datasets.  
- Convert audio data into spectrograms and evaluate preprocessing pipelines.  
- Develop semi-supervised autoencoder model for anomaly detection on healthy motor audio.  
- Evaluate reconstruction error distributions to establish anomaly detection thresholds.  
- Investigate supervised ML approaches (e.g., DeepONet or alternatives) for UAV battery health monitoring.  
- Train and validate ML models using induced fault datasets and battery profiles.  
- Conduct hyperparameter tuning for both autoencoder and supervised models.  
- Benchmark model performance (precision, recall, F1) against UAV health monitoring objectives.  
- Document AI methodology and results for inclusion in project reports and publications.  

## Siddharth Urankar (CS) – Software, Integration, Deployment

- Install and configure Linux OS on NVIDIA Jetson for UAV onboard computing.  
- Develop microphone interface software to support synchronized acoustic data capture.  
- Implement real-time data logging system for motor audio during UAV operation.  
- Optimize data storage format for efficiency in transfer and later ML model use.  
- Deploy trained autoencoder model onto Jetson for onboard inference.  
- Develop anomaly detection pipeline that integrates audio capture with autoencoder output.  
- Test latency and throughput of model inference on Jetson under flight-like conditions.  
- Implement battery data collection interface for supervised RUL prediction model.  
- Optimize Jetson codebase to balance recording, inference, and data transfer simultaneously.  
- Validate end-to-end system integration by running real-time UAV health monitoring tests.  
