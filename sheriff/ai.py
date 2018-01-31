import numpy as np
import random
import math
import gym


class MDP(gym.Env):
    """ Extension of OpenAI gym to Markov Decision Process (MDP) """
    action_map = {}
    observation_map = {}
    discount_factor = 0.95

    def transition(self, observation, action):
        """ Return transition to where the action makes the MDP transition to from observation. """
        raise NotImplementedError


def extract_policy(mdp, value):
    """ Extract and return optimal policy from value function of the MDP.
    For each state of the MDP, the action to be executed by the policy is set to:
        policy[state] = argmax(expected_payoff[action])
    """
    assert type(mdp.action_space) == gym.spaces.Discrete
    assert type(mdp.observation_space) == gym.spaces.Discrete

    policy = np.ndarray(shape=[mdp.observation_space.n], dtype=np.int)
    for observation in range(mdp.observation_space.n):
        optimal_value, optimal_action = -math.inf, mdp.action_space.sample()
        for action in range(mdp.action_space.n):
            transition, _ = mdp.transition(observation, action)
            if optimal_value <= value[transition]:
                optimal_value, optimal_action = value[transition], action
        policy[observation] = optimal_action

    return policy


def value_iteration(mdp, max_iter=100):
    """ Find and return the optimal policy for the MDP.
    The function uses the following version of the value iteration algorithm:
        0. Set value function for all states to 0.
        1. For every state update the value function to:
              value[state] = optimal_reward + discount_factor * optimal_payoff
           Where optimal_payoff is the maximum of expected payoffs when taking
           each action allowed from the current state. optimal_reward for the
           the action that achieves optimal_payoff.
        2. Goto 1. unless max_iter is reached.
        3. Extract the final optimal policy from the value function.
    """
    assert type(mdp.action_space) == gym.spaces.Discrete
    assert type(mdp.observation_space) == gym.spaces.Discrete

    value = np.zeros(shape=[mdp.observation_space.n])
    for _ in range(max_iter):
        for observation in range(mdp.observation_space.n):
            optimal_value, optimal_reward = -math.inf, -math.inf
            for action in range(mdp.action_space.n):
                transition, reward = mdp.transition(observation, action)
                if optimal_value <= value[observation]:
                    optimal_value, optimal_reward = value[transition], reward
            value[observation] = optimal_reward + mdp.discount_factor * optimal_value

    policy = extract_policy(mdp, value)
    return policy


def policy_iteration(mdp, max_iter=10):
    """ Find and return the optimal policy for the MDP.
    The function uses the following version of the policy iteration algorithm:
        0. Choose a random policy
        1. Solve Bellman's system of linear equations and get the value function for the policy.
        2. Extract new policy from the value function.
        3. Goto 1. unless max_iter is reached.
    """
    assert type(mdp.action_space) == gym.spaces.Discrete
    assert type(mdp.observation_space) == gym.spaces.Discrete

    policy = np.array([mdp.action_space.sample() for _ in range(mdp.observation_space.n)], dtype=np.int)
    for _ in range(max_iter):
        bellman_matrix = np.zeros(shape=[mdp.observation_space.n, mdp.observation_space.n])
        bellman_reward = np.zeros(shape=[mdp.observation_space.n])
        for observation in range(mdp.observation_space.n):
            action = policy[observation]
            transition, reward = mdp.transition(observation, action)
            bellman_matrix[observation, transition] = -mdp.discount_factor
            bellman_matrix[observation, observation] = 1
            bellman_reward[transition] = reward
        value = np.linalg.solve(bellman_matrix, bellman_reward)
        policy = extract_policy(mdp, value)

    return policy


def q_learning(env, learning_rate=0.2, exploration_rate=0.3, max_episodes=100, discount_factor=0.9):
    """ Find and return the optimal policy for the OpenAI Env.
    The function uses the following version of the Q learning algorithm:
        0. Choose a random action with probability exploration_rate and otherwise pick best known action from Q.
        1. Take a step with the environment to obtain the new observation and reward.
        2. Update the Q function with the new value and respect to the learning_rate:
              reward + discount_factor * max(Q[state, :])
        3. Goto 0. unless the environment has finished.
    """
    assert type(env.action_space) == gym.spaces.Discrete
    assert type(env.observation_space) == gym.spaces.Discrete

    Q = np.zeros(shape=[env.observation_space.n, env.action_space.n])
    for episode in range(max_episodes):
        observation = env.reset()

        done = False
        while not done:
            if random.uniform(0, 1) <= exploration_rate:
                action = env.action_space.sample()
            else:
                action = np.argmax(Q[observation, :])
            transition, reward, done, info = env.step(action)
            Q[observation, action] *= (1 - learning_rate)
            Q[observation, action] += learning_rate * (reward + discount_factor * np.max(Q[transition, :]))
            observation = transition

    policy = np.argmax(Q, axis=1)
    return policy
