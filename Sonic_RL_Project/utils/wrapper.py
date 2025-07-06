#utils/wrapper.py

from utils.logger import get_logger



class RewardShapingWrapper(gym.Wrapper):
    """

    Reward considerations:
    Rings: +100 per ring collected
    Kill enemies: +50
    Die to enemies: -25
    Ring < 1: -10 per second
    Time: +1500 - [time]
    Standing still: -500 per second not moving


    """
    def step(self, action):
        """
        """
        