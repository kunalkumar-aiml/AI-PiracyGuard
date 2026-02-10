# AI-PiracyGuard  

AI-PiracyGuard is a modular Python-based prototype system designed to detect and analyze pirated and manipulated video content. The project demonstrates how different software components can work together in an AI-based monitoring pipeline.

## What the system does
- Automatically scans uploaded videos  
- Estimates risk using a simple model  
- Flags suspicious content with alerts  
- Maintains activity logs  
- Generates text reports  
- Displays a visual summary of results  

## Project Structure
- scanner.py – finds new video uploads  
- risk_model.py – calculates basic risk score  
- alerts_v2.py – generates smart alerts  
- dashboard.py – shows live status  
- logger.py – records system activity  
- report_generator.py – creates reports  
- visualizer.py – displays summary results  
- pipeline.py – runs everything end-to-end  

## How to run
1. Run `main.py` to initialize the system  
2. Run `pipeline.py` to execute the full workflow  

This is a learning project aimed at understanding how AI, automation, and software modules can be integrated into a single working system.

Author: Kunal Kumar  
