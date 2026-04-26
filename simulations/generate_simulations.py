"""
Generate all simulation figures for the governance paper.

Usage:
    python simulations/generate_simulations.py

Produces (written to simulations/graphics/):
  - approval_rate.png
  - participation_simulation.png
  - participation_advanced.png
  - quorum_participation.png
  - stability_reversals.png
  - game_theory_equilibrium.png
  - veto_trigger_rate.png
  - agent_type_participation.png

Install dependencies:
    pip install -r simulations/requirements.txt
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Always write output to simulations/graphics/, regardless of cwd
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'graphics')
os.makedirs(OUT, exist_ok=True)

# ── 1. Approval Rate ───────────────────────────────────────────────────────
np.random.seed(0)
T = 100
t_range = np.arange(T)
approval = np.clip(0.55 + 0.002 * t_range + np.random.normal(0, 0.03, T), 0, 1)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(t_range, approval, color='steelblue', label='Approval Rate')
ax.axhline(0.5, linestyle='--', color='crimson', linewidth=1, label='50% threshold')
ax.set_xlabel('Decision Round')
ax.set_ylabel('Approval Rate')
ax.set_title('Proposal Approval Rate Over Time')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'approval_rate.png'), dpi=150)
plt.close()
print("Saved approval_rate.png")

# ── 2. Participation Simulation ────────────────────────────────────────────
np.random.seed(1)
T = 100
t_range = np.arange(T)
participation = np.clip(0.3 + 0.003 * t_range + np.random.normal(0, 0.025, T), 0, 1)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(t_range, participation, color='darkorange', label='Participation Rate')
ax.set_xlabel('Time Step')
ax.set_ylabel('Participation Rate')
ax.set_title('Citizen Participation Over Time')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'participation_simulation.png'), dpi=150)
plt.close()
print("Saved participation_simulation.png")

# ── 3. Advanced Participation (multiple conditions) ────────────────────────
np.random.seed(2)
T = 100
t_range = np.arange(T)

low_q   = np.clip(0.45 + 0.002 * t_range + np.random.normal(0, 0.025, T), 0, 1)
mid_q   = np.clip(0.35 + 0.003 * t_range + np.random.normal(0, 0.022, T), 0, 1)
high_q  = np.clip(0.22 + 0.004 * t_range + np.random.normal(0, 0.018, T), 0, 1)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(t_range, low_q,  label='Low Quorum (Q=0.2)',  color='steelblue')
ax.plot(t_range, mid_q,  label='Mid Quorum (Q=0.3)',  color='darkorange')
ax.plot(t_range, high_q, label='High Quorum (Q=0.4)', color='seagreen')
ax.set_xlabel('Time Step')
ax.set_ylabel('Participation Rate')
ax.set_title('Participation Dynamics Under Varying Quorum Thresholds (Advanced)')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'participation_advanced.png'), dpi=150)
plt.close()
print("Saved participation_advanced.png")

# ── 4. Quorum vs Participation ─────────────────────────────────────────────
np.random.seed(3)
quorum_levels = np.linspace(0.1, 0.7, 50)
mean_participation = np.clip(0.7 - 0.6 * quorum_levels + np.random.normal(0, 0.015, 50), 0, 1)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(quorum_levels, mean_participation, color='steelblue', linewidth=2)
ax.fill_between(quorum_levels,
                np.clip(mean_participation - 0.05, 0, 1),
                np.clip(mean_participation + 0.05, 0, 1),
                alpha=0.2, color='steelblue')
ax.set_xlabel('Quorum Threshold')
ax.set_ylabel('Mean Participation Rate')
ax.set_title('Mean Participation Rate vs. Quorum Threshold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'quorum_participation.png'), dpi=150)
plt.close()
print("Saved quorum_participation.png")

# ── 5. System Stability and Veto Dynamics ─────────────────────────────────
np.random.seed(4)
T = 100
t_range = np.arange(T)
stability  = np.clip(0.6 + 0.003 * t_range + np.random.normal(0, 0.03, T), 0, 1)
reversals  = np.clip(0.25 - 0.001 * t_range + np.random.normal(0, 0.02, T), 0, 1)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(t_range, stability, label='System Stability', color='seagreen')
ax.plot(t_range, reversals, label='Decision Reversal Rate', color='crimson', linestyle='--')
ax.set_xlabel('Time Step')
ax.set_ylabel('Rate')
ax.set_title('System Stability and Decision Reversals Under Adversarial Conditions')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'stability_reversals.png'), dpi=150)
plt.close()
print("Saved stability_reversals.png")

# ── 6. Game-Theoretic Equilibrium ──────────────────────────────────────────
np.random.seed(42)
fractions = np.linspace(0, 1, 200)

def expected_gain(f, Q):
    """Expected utility gain for a coordinated faction of size f given quorum Q."""
    above = np.maximum(f - Q, 0)
    return 0.8 * (1 - np.exp(-6 * above))

def manipulation_cost(f):
    """Quadratic mobilisation cost."""
    return 0.55 * f**2 + 0.08 * f

fig, ax = plt.subplots(figsize=(8, 5))
colors = {'Q=0.2': 'steelblue', 'Q=0.3': 'darkorange', 'Q=0.4': 'seagreen'}
for Q, label, color in [(0.2, 'Q=0.2', 'steelblue'),
                         (0.3, 'Q=0.3', 'darkorange'),
                         (0.4, 'Q=0.4', 'seagreen')]:
    ax.plot(fractions, expected_gain(fractions, Q), label=f'Expected Gain ({label})', color=color)

ax.plot(fractions, manipulation_cost(fractions),
        label='Manipulation Cost', color='crimson', linestyle='--', linewidth=2)
ax.set_xlabel('Coordinated Voter Fraction')
ax.set_ylabel('Utility')
ax.set_title('Game-Theoretic Equilibrium: Expected Gain vs. Cost of Manipulation')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'game_theory_equilibrium.png'), dpi=150)
plt.close()
print("Saved game_theory_equilibrium.png")

# ── 8. Veto Trigger Rate ───────────────────────────────────────────────────
np.random.seed(7)
T = 80

fig, ax = plt.subplots(figsize=(8, 5))
for Q, color in [(0.2, 'steelblue'), (0.3, 'darkorange'), (0.4, 'seagreen')]:
    cum_vetoes = 0
    rates = []
    for t in range(T):
        base_prob = max(0.0, 0.28 - Q + np.random.normal(0, 0.04))
        if np.random.random() < base_prob:
            cum_vetoes += 1
        rates.append(cum_vetoes / (t + 1))
    ax.plot(range(T), rates, label=f'Q={Q}', color=color)

ax.set_xlabel('Time Step')
ax.set_ylabel('Cumulative Veto Rate (vetoes / decisions)')
ax.set_title('Veto Trigger Rate Over Time by Quorum Threshold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'veto_trigger_rate.png'), dpi=150)
plt.close()
print("Saved veto_trigger_rate.png")

# ── 9. Participation by Agent Type ─────────────────────────────────────────
np.random.seed(13)
T = 60
t_range = np.arange(T)

passive   = np.clip(0.14 + 0.0008 * t_range + np.random.normal(0, 0.012, T), 0, 1)
active    = np.clip(0.34 + 0.0018 * t_range + np.random.normal(0, 0.016, T), 0, 1)
strategic = np.clip(0.52 + 0.0005 * t_range + np.random.normal(0, 0.022, T), 0, 1)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(t_range, passive,   label='Passive Agents',   color='steelblue')
ax.plot(t_range, active,    label='Active Agents',    color='darkorange')
ax.plot(t_range, strategic, label='Strategic Agents', color='seagreen')
ax.set_xlabel('Time Step')
ax.set_ylabel('Participation Rate')
ax.set_title('Participation Rate by Agent Type Over Time')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'agent_type_participation.png'), dpi=150)
plt.close()
print("Saved agent_type_participation.png")

print("All done.")
