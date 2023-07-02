import math
import random
from itertools import count

import torch
from torch import nn

from Game import possible_moves
from Network import Network
from GameEnv import GameEnv
import torch.optim as optim
import matplotlib.pyplot as plt
from ReplayMemory import ReplayMemory, Transition
from IPython import display


class Learn:

    def __init__(self):
        self.BATCH_SIZE = 16
        self.GAMMA = 0.99
        self.EPS_START = 0.9
        self.EPS_END = 0.05
        self.EPS_DECAY = 1000
        self.TAU = 0.005
        self.LR = 1e-3
        self.MEM_SIZE = 10000

        self.durations = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.env = GameEnv()
        n_actions = possible_moves.n_moves  # remove
        state, info = self.env.reset()
        n_observations = len(state)
        self.policy_net = Network(n_observations, n_actions).to(self.device)
        self.target_net = Network(n_observations, n_actions).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.optimizer = optim.AdamW(self.policy_net.parameters(), lr=self.LR, amsgrad=True)
        self.memory = ReplayMemory(self.MEM_SIZE)
        self.steps_done = 0
        plt.ion()

    def select_action(self, state, legal_mask=None):
        eps_threshold = self.EPS_END + (self.EPS_START - self.EPS_END) * math.exp(-1. * self.steps_done / self.EPS_DECAY)
        self.steps_done += 1
        if random.random() > eps_threshold:
            with torch.no_grad():
                out = self.policy_net(state)
                if legal_mask is not None:
                    legal_mask = torch.unsqueeze(torch.from_numpy(legal_mask), 0)
                    out[legal_mask == False] = float('-inf')  # sus
                return out.max(1)[1].view(1, 1)
        else:
            return torch.tensor([[self.env.action_space.sample()]], device=self.device, dtype=torch.long)

    def optimize_model(self):
        if len(self.memory) < self.BATCH_SIZE:
            return
        transitions = self.memory.sample(self.BATCH_SIZE)
        batch = Transition(*zip(*transitions))

        # Compute a mask of non-final states and concatenate the batch elements
        # (a final state would've been the one after which simulation ended)
        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_state)), device=self.device, dtype=torch.bool)
        next = [s for s in batch.next_state if s is not None]
        if not next:
            return
        non_final_next_states = torch.cat(next)
        state_batch = torch.cat(batch.state)
        action_batch = torch.cat(batch.action)
        reward_batch = torch.cat(batch.reward)

        # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
        # columns of actions taken. These are the actions which would've been taken
        # for each batch state according to policy_net
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)

        # Compute V(s_{t+1}) for all next states.
        # Expected values of actions for non_final_next_states are computed based
        # on the "older" target_net; selecting their best reward with max(1)[0].
        # This is merged based on the mask, such that we'll have either the expected
        # state value or 0 in case the state was final.
        next_state_values = torch.zeros(self.BATCH_SIZE, device=self.device)
        with torch.no_grad():
            next_state_values[non_final_mask] = self.target_net(non_final_next_states).max(1)[0]
        # Compute the expected Q values
        expected_state_action_values = (next_state_values * self.GAMMA) + reward_batch

        # Compute Huber loss
        criterion = nn.SmoothL1Loss()
        loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        # In-place gradient clipping
        torch.nn.utils.clip_grad_value_(self.policy_net.parameters(), 100)
        self.optimizer.step()

    def learn(self, n_episodes, plot_training=True):
        self.durations = []
        for i in range(n_episodes):
            state, info = self.env.reset()
            state = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
            for t in count():
                action = self.select_action(state, legal_mask=self.env.game.legal_moves_mask())
                observation, reward, terminated, truncated, _ = self.env.step(action.item())
                reward = torch.tensor([reward], device=self.device)
                if terminated:
                    next_state = None
                else:
                    next_state = torch.tensor(observation, dtype=torch.float32, device=self.device).unsqueeze(0)
                self.memory.push(state, action, next_state, reward)
                state = next_state
                self.optimize_model()
                target_net_state = self.target_net.state_dict()
                policy_net_state = self.policy_net.state_dict()
                for key in policy_net_state:
                    target_net_state[key] = policy_net_state[key] * self.TAU + target_net_state[key] * (1 - self.TAU)
                self.target_net.load_state_dict(target_net_state)
                if terminated or truncated:
                    self.durations.append(t + 1)
                    if plot_training:
                        self.plot_durations()
                    break
        print('Complete')
        self.plot_durations(show_result=True)
        plt.ioff()
        plt.show()

    def plot_durations(self, show_result=False):
        plt.figure(1)
        durations_t = torch.tensor(self.durations, dtype=torch.float)
        if show_result:
            plt.title('Result')
        else:
            plt.clf()
            plt.title('Training...')
        plt.xlabel('Episode')
        plt.ylabel('Duration')
        plt.plot(durations_t.numpy())
        # Take 100 episode averages and plot them too
        if len(durations_t) >= 100:
            means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
            means = torch.cat((torch.zeros(99), means))
            plt.plot(means.numpy())

        plt.pause(0.001)  # pause a bit so that plots are updated

        if not show_result:
            display.display(plt.gcf())
            display.clear_output(wait=True)
        else:
            display.display(plt.gcf())


if __name__ == "__main__":
    l = Learn()
    l.learn(1000, plot_training=True)
