from DQN.q_network import ZombieQNetwork, ReplayBuffer
import random
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

class DQNAgent:
    def __init__(self, input_shape=(4, 11, 11), num_actions=5, learning_rate=0.001):
        print("Initializing DQN Agent...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # --- 1. Mózgi Agenta (Policy i Target) ---
        self.policy_net = ZombieQNetwork(input_shape, num_actions).to(self.device)
        self.target_net = ZombieQNetwork(input_shape, num_actions).to(self.device)
        
        # Kopiujemy wagi początkowe
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval() # TargetNet nie uczy się bezpośrednio
        
        # --- 2. Narzędzia ---
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.memory = ReplayBuffer(capacity=10000)
        
        # --- 3. Hiperparametry ---
        self.batch_size = 64
        self.gamma = 0.99       # Współczynnik dyskontowania (jak ważna jest przyszłość)
        self.epsilon = 1.0      # Eksploracja (na początku 100% losowych ruchów)
        self.epsilon_min = 0.05 # Minimalna eksploracja
        self.epsilon_decay = 0.995 # Jak szybko przestajemy losować
        self.update_target_every = 1000 # Co ile kroków aktualizujemy TargetNet
        self.step_counter = 0

    def get_action(self, state):
        """Podejmuje decyzję na podstawie stanu (4, 11, 11)"""
        # Epsilon-Greedy Strategy
        if random.random() < self.epsilon:
            return random.randint(0, 4) # Losowa akcja (eksploracja)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device) # Dodajemy wymiar batcha: (1, 4, 11, 11)
        
        with torch.no_grad():
            q_values = self.policy_net(state_tensor)
            
        return q_values.argmax().item() # Wybierz akcję z największym Q

    def learn(self):
        """Główna pętla uczenia sieci"""
        if len(self.memory) < self.batch_size:
            return # Za mało danych, żeby się uczyć

        # 1. Pobierz losową paczkę z pamięci (Experience Replay)
        state, action, reward, next_state, done = self.memory.sample(self.batch_size)

        state = torch.FloatTensor(state).to(self.device)
        next_state = torch.FloatTensor(next_state).to(self.device)
        action = torch.LongTensor(action).unsqueeze(1).to(self.device)
        reward = torch.FloatTensor(reward).unsqueeze(1).to(self.device)
        done = torch.FloatTensor(done).unsqueeze(1).to(self.device)

        # 2. Oblicz Q(s, a) z PolicyNet
        # gather wybiera Q-wartość tylko dla akcji, którą faktycznie wykonaliśmy
        q_values = self.policy_net(state).gather(1, action)

        # 3. Oblicz Q_target(s', a') z TargetNet
        with torch.no_grad():
            next_q_values = self.target_net(next_state).max(1)[0].unsqueeze(1)
            # Wzór Bellmana: R + gamma * max(Q_next)
            # Jeśli done=1 (koniec gry), to nie ma przyszłości, zostaje samo R.
            expected_q_values = reward + (self.gamma * next_q_values * (1 - done))

        # 4. Oblicz błąd (Loss) i zrób krok optymalizacji
        loss = F.mse_loss(q_values, expected_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 5. Aktualizacja Epsilona (zmniejszamy losowość)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # 6. Aktualizacja Target Network (Stabilizacja)
        self.step_counter += 1
        if self.step_counter % self.update_target_every == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
            print("--- Target Network Updated ---")