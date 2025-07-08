#scripts/train.py

from utils.logger import get_logger


import retro
import numpy as np

# Load the Sonic environment
env = retro.make(game='SonicTheHedgehog3-Genesis', state='Level1')
obs = env.reset()

total_reward = 0
done = False

print("Starting test episode...")

while not done:
    env.render()
    
    # Take random actions for test
    action = env.action_space.sample()
    obs, reward, done, info = env.step(action)
    total_reward += reward

print("Test episode finished.")
print(f"Total Reward: {total_reward}")
env.close()
