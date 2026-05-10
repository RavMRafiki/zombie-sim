from typing import Any

from DQN.q_network import ZombieQNetwork, ReplayBuffer
import logging
import random
import numpy as np
import torch
import torch.optim as optim
import torch.nn.functional as F


class DQNAgent:
    def __init__(
        self, input_shape=(4, 11, 11), num_actions=5, learning_rate=0.001, vector_size=2
    ) -> None:
        logging.info("Initializing DQN Agent...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # --- 1. Mózgi Agenta (Policy i Target) ---
        self.policy_net: ZombieQNetwork[Any, int, int] = ZombieQNetwork(input_shape, num_actions, vector_size).to(
            self.device
        )
        self.target_net: ZombieQNetwork[Any, int, int] = ZombieQNetwork(input_shape, num_actions, vector_size).to(
            self.device
        )

        # Kopiujemy wagi początkowe
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # TargetNet nie uczy się bezpośrednio

        # --- 2. Narzędzia ---
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.memory: ReplayBuffer[int] = ReplayBuffer(capacity=10000)

        # --- 3. Hiperparametry ---
        self.batch_size = 64
        self.gamma = 0.99  # Współczynnik dyskontowania (jak ważna jest przyszłość)
        self.epsilon = 1.0  # Eksploracja (na początku 100% losowych ruchów)
        self.epsilon_min = 0.05  # Minimalna eksploracja
        self.epsilon_decay = 0.995  # Jak szybko przestajemy losować
        self.update_target_every = 1000  # Co ile kroków aktualizujemy TargetNet
        self.step_counter = 0

    def get_action(self, state) -> int | Any:
        """Podejmuje decyzję na podstawie stanu (4, 11, 11)"""
        # state to teraz krotka: (grid_obs, vector_obs)
        grid_obs, vector_obs = state

        if random.random() < self.epsilon:
            return random.randint(0, 4)

        # Zamiana na tensory i dodanie wymiaru batch (unsqueeze)
        grid_tensor: torch.Tensor = torch.FloatTensor(grid_obs).unsqueeze(0).to(self.device)
        vec_tensor: torch.Tensor = torch.FloatTensor(vector_obs).unsqueeze(0).to(self.device)

        with torch.no_grad():
            q_values = self.policy_net(grid_tensor, vec_tensor)

        return q_values.argmax().item()  # Wybierz akcję z największym Q

    def learn(self) -> None:
        if len(self.memory) < self.batch_size:
            return

        # Rozpakowujemy na kolumny.
        # Zmienna 'state' to teraz lista krotek: ((img1, vec1), (img2, vec2)...)
        state, action, reward, next_state, done = self.memory.sample(self.batch_size)

        # --- TUTAJ JEST MAGIA ROZDZIELANIA ---

        # Rozdzielamy 'state' na listę obrazków i listę wektorów
        state_imgs, state_vecs = zip(*state)
        # To samo dla 'next_state'
        next_state_imgs, next_state_vecs = zip(*next_state)

        # 2. Tworzymy Tensory (osobno dla obrazów, osobno dla wektorów)

        # A. Obrazy
        state_imgs: torch.Tensor = torch.FloatTensor(np.array(state_imgs)).to(self.device)
        next_state_imgs: torch.Tensor = torch.FloatTensor(np.array(next_state_imgs)).to(self.device)

        # B. Wektory
        state_vecs: torch.Tensor = torch.FloatTensor(np.array(state_vecs)).to(self.device)
        next_state_vecs: torch.Tensor = torch.FloatTensor(np.array(next_state_vecs)).to(self.device)

        # C. Reszta (bez zmian)
        action: torch.Tensor = torch.LongTensor(action).unsqueeze(1).to(self.device)
        reward: torch.Tensor = torch.FloatTensor(reward).unsqueeze(1).to(self.device)
        done: torch.Tensor = torch.FloatTensor(done).unsqueeze(1).to(self.device)

        # 3. Oblicz Q(s, a)
        # Podajemy sieci DWA argumenty: obrazki i wektory
        q_values = self.policy_net(state_imgs, state_vecs).gather(1, action)

        # 4. Oblicz Q_target
        with torch.no_grad():
            # Tutaj też podajemy dwa argumenty do TargetNet
            next_q_values = (
                self.target_net(next_state_imgs, next_state_vecs).max(1)[0].unsqueeze(1)
            )
            expected_q_values = reward + (self.gamma * next_q_values * (1 - done))

        # 5. Loss i optymalizacja (bez zmian)
        loss: torch.Tensor = F.mse_loss(q_values, expected_q_values)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Reszta funkcji (epsilon, target update) bez zmian...
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        self.step_counter += 1
        if self.step_counter % self.update_target_every == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
            logging.info("--- Target Network Updated ---")
