import sys
import random
import bisect
import itertools
import collections
import numpy as np


class MDP:
    """ Abstract Markov Decision Process (MDP), defined by an initial state, list of states, list of actions,
     transition model, and reward function. The class also holds the discount rate gamma and terminal states. """
    def __init__(self, state: object, states: list, actions: list, terminals: set, gamma: float = 0.9):
        """ Construct the MDP from initial state, list of states/actions, terminal states and discount rate. """
        if state not in states:
            raise ValueError
        self.state = state
        self.states = states
        self.actions = actions
        self.terminals = terminals
        self.gamma = gamma

    def action(self, action: object):
        """ Perform action on the MDP and update the current state. """
        if action is None:
            return self.state
        choices = self.transitions(self.state, action)
        target_states, target_probabilities = zip(*choices)
        target_cumulative_probabilities = list(itertools.accumulate(target_probabilities))
        target_idx = bisect.bisect(target_cumulative_probabilities, random.random())
        self.state = target_states[target_idx]

    def transitions(self, state: object, action: object) -> list:
        """ Transition model of the MDP.
        From a state and an action, return a list of (transition state,
        transition probability) tuple pairs. Transition probabilities must form a distribution and therefore
        sum to 1 without being negative. """
        raise NotImplementedError

    def reward(cls, state: object = None) -> float:
        """ Numeric value of the reward for the state or the current state of the MDP is no state is provided. """
        raise NotImplementedError

    def reset(self):
        """ Reset MDP to it's initial state. Useful after the MDP has finished and reached a terminal state. """
        raise NotImplementedError

    def finished(self, state: object = None) -> bool:
        """ Check if the MDP has reached one of it's terminal states. """
        if state is None:
            state = self.state
        return state in self.terminals

    def states_vismap(self) -> dict:
        """ Return state visualization dictionary that maps each state to a string. """
        return {state: str(state) for state in self.states}

    def actions_vismap(self) -> dict:
        """ Return action visualization dictionary that maps action state to a string. """
        return {action: str(action) for action in self.actions}

    def __repr__(self) -> str:
        vismap = self.states_vismap()
        visuals = [vismap[state] for state in self.states]
        return ''.join(visuals)


class SheriffChase1D(MDP):
    """ Simple 1D criminal chase game implemented as a Markov Decision Process (MDP).
    The goal is to catch the criminal ◯ and avoid prison ✖ by moving the sheriff ★ left or right. """
    def __init__(self):
        """ Construct the sheriff Chase1D game MDP. """
        states = [i for i in range(10)]
        actions = [-1, +1]
        self.criminal, self.prison = random.sample(states, 2)
        terminals = {self.criminal, self.prison}
        super().__init__(states[0], states, actions, terminals, gamma=0.9)
        self.reset()

    def reward(self, state: object = None) -> float:
        """ Return +1 for catching the criminal, -1 for getting into prison and 0 otherwise. """
        if state is None:
            state = self.state
        if state == self.criminal:
            return +1.0
        if state == self.prison:
            return -1.0
        return 0.0

    def transitions(self, state: object, action: object) -> list:
        """ Non-stochastic MDP dynamics. Sheriff isn't drunk and gets where he wants to. """
        if self.finished(state):
            return []
        target_state = self.states[(state + action) % len(self.states)]
        target_probability = 1.0
        return [(target_state, target_probability)]

    def reset(self):
        """ Reset sheriff into a random initial location that isn't prison or criminal. """
        self.state = random.choice(self.states)
        while self.state in self.terminals:
            self.state = random.choice(self.states)

    def states_vismap(self) -> dict:
        """ Some swag for nice prints of game states. """
        vismap = collections.defaultdict(lambda: "-")
        vismap.update({self.criminal: "◯", self.prison: "✖", self.state: "★"})
        return vismap

    def actions_vismap(self) -> dict:
        """ Some swag for nice prints of policies. """
        return {-1: "<", +1: ">"}


class ReinforcementLearning:
    """ A tool-set of functions for finding optimal policy for a given Markov Decision Process (MDP).
    The tool-set internals take advantage of action-value function that ultimately gives the expected payoff of taking
    an action from a given state and following the optimal policy. """
    class Policy(dict):
        """ Set of rules that the MDP follows in selecting actions.
        Rules are implemented as a dictionary where keys are states and values are actions to be executed. """
        def __init__(self, mdp: MDP, dict: dict = None):
            """ Construct policy for an MDP taking steps from the provided dict. """
            super().__init__()
            if dict is not None:
                self.update(dict)
            self.mdp = mdp

        @classmethod
        def extract(cls, mdp: MDP, value_function: dict) -> object:
            """ Extract and return optimal policy from an MDP and it's value function.
            For each state of the MDP, the action to be executed by the policy is set to:
                policy[state] = argmax(expected payoff from taking action) """
            policy = cls(mdp)
            for state in mdp.states:
                optimal_payoff, optimal_action = 0, random.choice(mdp.actions)
                for action in mdp.actions:
                    action_payoff = 0
                    for trans_state, trans_probability in mdp.transitions(state, action):
                        action_payoff += value_function[trans_state] * trans_probability
                    if optimal_payoff < action_payoff:
                        optimal_payoff, optimal_action = action_payoff, action
                policy[state] = optimal_action
            return policy

        def __repr__(self):
            mdp = self.mdp
            actions_vismap = mdp.actions_vismap()
            visuals = [actions_vismap[self[state]] for state in mdp.states]
            states_vismap = mdp.states_vismap()
            for terminal in mdp.terminals:
                visuals[mdp.states.index(terminal)] = states_vismap[terminal]
            return ''.join(visuals)

    @classmethod
    def value_iteration(cls, mdp: MDP, max_iter: int = 10) -> Policy:
        """ Find and return the optimal policy for the MDP.
        The function uses the following version of the value iteration algorithm:
            0. Set value function for all states to 0.
            1. For every state update the value function to:
                  value[state] = reward[state] + gamma * optimal_payoff
               Where optimal_payoff is the maximum of expected payoffs when taking
               each action allowed from the current state.
            2. Goto 1. unless max_iter is reached.
            3. Extract the final optimal policy from the value function. """
        value = {state: 0 for state in mdp.states}
        for _ in range(max_iter):

            for state in mdp.states:
                optimal_payoff = 0
                for action in mdp.actions:
                    action_payoff = 0
                    for trans_state, trans_probability in mdp.transitions(state, action):
                        trans_idx = mdp.states.index(trans_state)
                        action_payoff += value[trans_idx] * trans_probability
                    optimal_payoff = max(optimal_payoff, action_payoff)

                value[state] = mdp.reward(state) + mdp.gamma * optimal_payoff

        policy = cls.Policy.extract(mdp, value)
        return policy

    @classmethod
    def policy_iteration(cls, mdp: MDP, max_iter: int = 5) -> Policy:
        """ Find and return the optimal policy for the MDP.
        The function uses the following version of the policy iteration algorithm:
            0. Choose a random policy
            1. Solve Bellman's system of linear equations and get the value function for the policy.
            2. Extract new policy from the value function.
            3. Goto 1. unless max_iter is reached. """
        policy = cls.Policy(mdp, {state: random.choice(mdp.actions) for state in mdp.states})
        bellman_matrix = np.empty(shape=[len(mdp.states), len(mdp.states)])
        reward = np.empty(shape=[len(mdp.states), 1])
        for _ in range(max_iter):

            bellman_matrix[:, :], reward[:] = 0, 0
            for idx, state in enumerate(mdp.states):
                for trans_state, trans_probability in mdp.transitions(state, policy[state]):
                    trans_idx = mdp.states.index(trans_state)
                    bellman_matrix[idx, trans_idx] = - mdp.gamma * trans_probability
                bellman_matrix[idx, idx] += 1
                reward[idx] = mdp.reward(state)

            value = np.linalg.solve(bellman_matrix, reward)
            policy = cls.Policy.extract(mdp, {state: value[idx, 0] for idx, state in enumerate(mdp.states)})

        return policy


if __name__ == "__main__":
    game = SheriffChase1D()
    actions_keymap = {"l": game.actions[0], "r": game.actions[1]}
    policy = ReinforcementLearning.policy_iteration(mdp=game)
    print("Catch criminal ◯ and avoid prison ✖. You are the sheriff ★ who moves left and right.")
    print("|{policy}|  Hint".format(policy=policy))

    while not game.finished():
        prompt = "|{game}|  L <★> R : ".format(game=game)
        key = input(prompt)[0].lower()
        game.action(actions_keymap.get(key, None))

    if game.reward() > 0:
        print("You won :)")
        sys.exit(0)
    if game.reward() < 0:
        print("You lost :(")
        sys.exit(1)
