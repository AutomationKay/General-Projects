# Sonic Reinforcement Learning Project 
![Sonic Gameplay](images/sonic_logo.gif)

The purpose of this project is to train a reinforcement learning agent to play **Sonic the Hedgehog 3** using `openai gymnasium`, the `stable-retro` environment, and the `Stable-Baselines3` library with the PPO algorithm.

---

## Project Structure

```
sonic_rl_project/
├── envs/
│   └── sonic_env.py        # Loads and wraps the Sonic environment
├── images/                 # Images for markdown and screenshots of the training process
├── logs/                   # TensorBoard logs
├── models/                 # Saved model and model checkpoints
├── scripts/
│   ├── evaluate.py         # Evaluation script
│   └── train.py            # Main training script
├── utils/
|   ├── wrappers.py         # Frame stack, grayscale, resize, etc
│   └── logger.py           # Customer logger for debugging throughout the project
├── videos/                 # Saved gameplay videos
└── README.md               # This file
```

---

## How Everything Connects

- `train.py`: Main script that:
  - Imports `make_env()` from `envs/sonic_env.py`
  - Applies preprocessing from `utils/wrappers.py`
  - Trains the agent using PPO and logs progress
  - Saves the model to `/models/`
  - Logs training data to `/logs/` for TensorBoard

- `evaluate.py`: Loads a trained model and renders the game.

- `sonic_env.py`: Defines `make_env()` which:
  - Loads the Sonic ROM via `retro.make()`
  - Wraps the environment using functions in `wrappers.py`

- `wrappers.py`: Custom preprocessing such as:
  - Resize frames to (84, 84)
  - Convert to grayscale
  - Stack last 4 frames

- `logger.py`: Custom logger for debugging and gathering info.

---

## 📊 Monitoring Training

1. Train the agent:
   ```bash
   python scripts/train.py
   ```

2. Monitor with TensorBoard:
   ```bash
   tensorboard --logdir logs/
   ```

This will open a browser where you can view:
- Reward over time
- Loss curves
- Policy entropy
- Time steps

---

## 📦 Sonic ROM and Emulator
  1. Download the ROM for Sonic 3 legally.
  2. Import it with:
     ```python
     import retro
     retro.import_roms("path/to/rom_directory")
     ```
  3. After importing, the ROM will be available to `stable-retro`.

---

## 📌 Requirements

- Python 3.8+
- `gymnasium`
- `stable-retro`
- `stable-baselines3`
- `pygame` (for rendering)
- `tensorboard`

Install with:
```bash
pip install -r requirements.txt
```

---

## Now Play
Enjoy watching Sonic get smarter!
![Sonic Gameplay](images/sonic_running.gif)