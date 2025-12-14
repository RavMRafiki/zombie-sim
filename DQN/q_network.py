import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
from collections import deque

class ZombieQNetwork(nn.Module):
    def __init__(self, input_shape, num_actions):
        super(ZombieQNetwork, self).__init__()
        # input_shape to (4, 11, 11) -> (Channels, Height, Width)
        
        # Warstwy konwolucyjne (widzenie przestrzenne)
        # Wejście: 4 kanały (klatki), Wyjście: 32 filtry, Kernel: 3x3
        self.conv1 = nn.Conv2d(in_channels=input_shape[0], out_channels=32, kernel_size=3, stride=1, padding=1)
        
        # Druga warstwa, żeby wyłapać bardziej złożone zależności
        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1, padding=1)
        
        # Obliczamy rozmiar po spłaszczeniu (Flatten)
        # Przy padding=1 i stride=1 wymiar 11x11 się nie zmienia.
        # Więc mamy 64 kanały * 11 * 11
        self.flatten_dim = 64 * 11 * 11
        
        # Warstwy gęste (podejmowanie decyzji)
        self.fc1 = nn.Linear(self.flatten_dim, 512)
        self.fc2 = nn.Linear(512, num_actions) # Wyjście: Q-value dla każdej akcji

    def forward(self, x):
        # x to tensor o wymiarach (Batch_Size, 4, 11, 11)
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        
        # Spłaszczenie obrazka do wektora
        x = x.view(x.size(0), -1) 
        
        x = F.relu(self.fc1(x))
        return self.fc2(x) # Zwraca Q-values, nie używamy Softmax w DQN!
    
class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        # State i next_state to tablice numpy (4, 11, 11)
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        # Losujemy paczkę wspomnień do nauki
        state, action, reward, next_state, done = zip(*random.sample(self.buffer, batch_size))
        return np.array(state), action, reward, np.array(next_state), done
    
    def __len__(self):
        return len(self.buffer)