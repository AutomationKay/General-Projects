# CARLA Reinforcement Learning Agent

This project trains a self-driving car agent using Reinforcement Learning in the CARLA simulator.

## Setup
1. Download CARLA from the [official releases page](https://github.com/carla-simulator/carla/releases) and extract it.
2. Make sure `CarlaUE4.exe` is running (use `-quality-level=Low` for low-end machines).
3. Clone this repo and install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
To collect data:
```bash
python scripts/collect_data.py
```

To train the agent:
```bash
python agent/train.py
```

## Project Structure
- `agent/`: Core RL training logic
- `scripts/`: Helper scripts for data collection
- `config/`: YAML files 
- `saved_models/`: Where trained policies are saved

## Requirements
- Python 3.8+
- CARLA 0.10.0
- NVIDIA GPU (recommended)
