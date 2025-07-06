#envs/sonic_env.py



from utils.logger import get_logger

class Sonic3Env(gym.Env):
    """
    Sonic The Hedgehog 3 Env
    --------------------

    Custom Gymnasium environment for training an agent to play Sonic the Hedgehog 3
    from start to finish in a given level.

    Environment Design Overview
    ===========================

    1. Skill Objective
    ------------------
    The agent should learn to complete a level in *Sonic the Hedgehog 3* from start 
    to finish, while avoiding death, collecting rings, and minimizing time.

    2. Observation Space
    --------------------
    The agent may be provided with:
    - Sonic's position and velocity
    - Elapsed level time
    - Current game state (e.g., air, ground, crouch)
    - Position and velocity of nearby enemies or hazards
    - Number of rings held

    This may be extracted from raw frames (pixel-based) or game memory (RAM-based).

    3. Action Space
    ---------------
    The agent can take the following actions:
    - LEFT            : Move left
    - RIGHT           : Move right
    - DOWN            : Duck (or roll when combined with motion)
    - JUMP            : Jump vertically
    - LEFT + JUMP     : Jump to the left
    - RIGHT + JUMP    : Jump to the right
    - DOWN + MOVE     : Roll or spin dash

    Actions can be implemented using a MultiBinary or MultiDiscrete space, depending
    on whether combinations of buttons are allowed simultaneously.

    4. Reward Function
    ------------------
    Success is measured by:
    - Reaching the level end (+1000 or more)
    - Holding rings (+1 per ring)
    - Finishing faster (e.g., +[300 - time])
    - Forward progress (+small reward for moving right)

    Penalities are oberserved when:
    - Standing still (-1000 per second standing still)
    - Moving backwards (-100 per backwards movement)
    - Dying (e.g. falling into pits, having 0 rings when being hit) (-1000)

    5. Episode Termination
    ----------------------
    Episodes end under any of the following conditions:
    - Agent runs out of lives
    - Agent finishes the level
    - Maximum time exceeded (e.g., 10 minutes or game over)

    This design defines clear learning cycles with success/failure boundaries.
    """