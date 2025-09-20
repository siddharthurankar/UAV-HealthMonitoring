# UAV-HealthMonitoring
Senior Design Project – UAV Powertrain Health Monitoring (Fall 2025)

# UAV Health Monitoring

## Team Members
- **Prissha Chawla (CS)** – prissha.chawla@uc.edu
- **Siddharth Urankar (CS)** – urankasa@mail.uc.edu
- **Ally Blair (ME)** – blairar@mail.uc.edu

## Faculty/Industry Advisors
- Dr. Manish Kumar (UC, Mechanical Engineering)
- Dr. Manuel Arias Chao (ZHAW, Switzerland)
- Dr. Chetan Kulkarni (NASA Ames)

## Project Summary
Our project develops a UAV powertrain health monitoring framework using machine learning to detect motor anomalies and predict battery degradation.  
- Motor health: semi-supervised 1D CNN Autoencoder trained on healthy BLDC motor acoustics.  
- Battery health: supervised DeepONet trained on voltage–current profiles to estimate degradation, Remaining Useful Life (RUL), and remaining flight time.  

This system will integrate both models to provide real-time in-flight diagnostics and preflight readiness checks, supporting UAV reliability in mission-critical operations.


UAV-HealthMonitoring/
│
├── README.md
├── Project-Description.md
│
├── PROFESSIONAL_BIOS/
│   ├── Siddharth_Urankar_Bio.md
│   ├── Prissha_Chawla_Bio.md
│   └── Ally_Blair_Bio.md
│
└── docs/
    ├── Advisor_Approval.pdf
    ├── Project_Decision_Framework.pdf
    └── References.md
