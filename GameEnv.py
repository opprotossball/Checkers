import gymnasium as gym
from gymnasium import spaces

from Game import Game, possible_moves


class GameEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}

    def __init__(self, render_mode=None, size=8):
        self.size = size
        self.game = Game(size)
        self.observation_space = spaces.Discrete(len(self.game.game_state))
        self.action_space = spaces.Discrete(possible_moves.n_moves)
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

    def reset(self, seed=None, options=None):
        self.game = Game(self.size)
        observation = self.game.game_state
        info = None
        if self.render_mode == "human":
            self._render_frame()
        return observation, info

    def step(self, action):
        valid = self.game.perform_move(possible_moves.move(action))
        if self.game.winner_side is not None:
            reward = 1
        elif not valid:
            reward = -1
        else:
            reward = 0

        observation = self.game.game_state
        info = None
        terminated = self.game.done or not valid

        if self.render_mode == "human":
            self._render_frame()

        return observation, reward, terminated, False, info

    def render(self):
        if self.render_mode == "rgb_array":
            return self._render_frame()

    def _render_frame(self):
        pass

    def close(self):
        pass
