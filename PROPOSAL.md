# GSoC 2026 Proposal — SITL Model Generation from Flight Data

---

## Contact Information

- Name: Aashrith Bandaru
- Email: bandaru6@illinois.edu
- GitHub: github.com/bandaru6
- LinkedIn: linkedin.com/in/aashrith-bandaru
- University: University of Illinois Urbana-Champaign
- Major: B.S. Computer Science + Statistics (Dual Degree)
- GPA: 3.83/4.0
- Location: Champaign, IL / Plano, TX (summer)

---

## Project

**Project Name:** SITL Model Generation from Flight Data

**Project Description:**

ArduPilot's Software-In-The-Loop (SITL) simulator is one of the most widely used tools in
the ArduPilot ecosystem, allowing developers to test autopilot code without real hardware.
However, SITL's default airframe models are generic — they do not reflect the specific
dynamics of individual vehicles. A quadcopter with heavier propellers, different motor
characteristics, or unusual battery chemistry will behave differently in the real world than in
simulation, and that gap makes SITL less useful for tuning, validation, and autonomy
development.

This project builds an end-to-end toolchain that takes real ArduPilot DataFlash flight logs
(.bin files), estimates the key vehicle dynamics and sensor parameters using grey-box system
identification, and outputs an updated SITL frame model (.json) and sensor parameter file
(.parm) that better matches the real vehicle. The output files are directly compatible with
ArduPilot's existing SITL infrastructure — the multicopter frame already supports loading
physics parameters from a JSON model file, and SITL exposes SIM_* parameters for sensor
noise, bias, and scale. The project targets those existing mechanisms rather than inventing new
formats.

The system also supports ArduPilot's dedicated SYSID mode, which injects chirp excitation
into control loops and logs synchronized stimulus/response data — the ideal input for
frequency-domain and time-domain parameter estimation.

**Deliverables:**

1. A Python CLI tool (log_to_model_params.py) that parses DataFlash .bin logs and runs
   the full system identification pipeline
2. A tuned JSON frame model output compatible with ArduPilot's multicopter SIM_Frame
3. A SIM_* sensor parameter .parm file (accelerometer/gyro bias, noise, scale)
4. A validation harness that compares the fitted SITL model against held-out log segments
   and reports quantitative sim-vs-real error metrics with confidence intervals
5. Documentation and a runbook for the full workflow, aligned with sim_vehicle.py usage

---

## Would you be willing to work on another project idea instead?

If SITL Model Generation were not available, I would be most interested in the AI-Assisted
Log Diagnosis and Root-Cause Detection project. My background in statistical modeling and
time-series analysis from both my Statistics degree and research at UIUC's BLENDER Lab
would apply directly — anomaly detection over flight telemetry shares the same core problem
structure as parameter estimation: extracting meaningful signal from noisy, high-dimensional
time-series data. I would approach it using feature engineering over log message sequences
and probabilistic classification, rather than black-box ML, to ensure the results are
interpretable and actionable for ArduPilot developers.

---

## Why I Am Interested in This Project

The core technical problem in SITL Model Generation is parameter estimation from noisy
time-series data under partial observability — you observe IMU measurements, motor commands,
and state estimates, but you never directly observe mass, inertia, or drag coefficients. You have
to infer them from indirect evidence, with noise and estimator bias in the signal chain. That is
exactly the kind of problem I have been building intuition for through my Statistics coursework
(Computational Linear Algebra, Statistical Computing, Applied ML) and through my research
at UIUC's BLENDER Lab.

At BLENDER Lab I build simulation evaluation pipelines for autonomous driving systems: C++
simulation components, trajectory rollout infrastructure, and counterfactual scenario pipelines
for causal inference and policy evaluation. The central challenge there is the same as in SITL —
making simulated behavior match real-world dynamics well enough that results in simulation
transfer to the real system. I have spent months thinking about where sim-to-real gaps come
from and how to measure and close them. The SITL project is that same problem applied to
flight dynamics, and it is one I find genuinely compelling.

Before writing this proposal, I set up the ArduPilot SITL environment locally, read through
the multicopter SIM_Frame code to understand what parameters the JSON model exposes, and
wrote a working log parser (using pymavlink DFReader_binary) that extracts hoverThrOut from
CTUN.ThO, propExpo from MOT_THST_EXPO, PWM range from RCOU, and battery parameters
from BAT messages, then outputs a starter JSON compatible with sim_vehicle.py. That code is
at github.com/bandaru6/gsoc-sitl-sysid.

I also read through the academic literature on multirotor system identification:
- Burri et al. (2020), "Identification of the Propeller Coefficients and Dynamic Parameters
  of a Hovering Quadrotor From Flight Data" — establishes the standard grey-box approach
  for thrust coefficient, drag, and inertia estimation from flight data
- Ljung (1999), "System Identification: Theory for the User" — the canonical reference on
  prediction error methods and maximum likelihood estimation
- Mahony et al. (2012), "Multirotor Aerial Vehicles" — covers the dynamics model
  structure I am replicating in the identification pipeline

The combination of my Statistics background, my active research in simulation evaluation, and
the work I have already done in the ArduPilot codebase makes me confident I can execute this
project well within the 350-hour scope.

---

## Proposed Architecture

The pipeline has five stages, each with a clear input/output contract:

```
Stage 1: Log Parser + Time Alignment
  Input:  ArduPilot DataFlash .bin log
  Output: Synchronized time-series DataFrame
          (IMU acc/gyro, RCOU motor commands, CTUN throttle,
           ATT attitude estimates, BAT battery state, GPS/EKF velocity)
  Tool:   pymavlink DFReader_binary; handles old (TimeMS) and new (TimeUS) formats
  Notes:  Resamples all message streams to a common timebase;
          segments flight into hover, maneuver, and idle windows

Stage 2: Segment Selector
  Input:  Synchronized time-series
  Output: Labeled windows — hover segments (low climb rate, stable attitude),
          step-response windows (rate steps for inertia ID),
          SYSID chirp windows (if SID messages present)
  Notes:  Quality filtering: rejects windows with GPS outages, EKF divergence,
          or insufficient excitation (condition number check)

Stage 3: Grey-Box Dynamics Optimizer
  Input:  Labeled windows + initial parameter guess (from SITL defaults or prior)
  Output: Fitted dynamics parameters:
          - hoverThrOut (throttle fraction at hover)
          - moment_of_inertia [Ixx, Iyy, Izz] (kg*m^2)
          - mdrag_coef (momentum drag coefficient)
          - disc_area (rotor disc area, m^2)
          - propExpo (thrust curve nonlinearity)
          - motor_spin_min, motor_spin_max (normalized)
  Method: Nonlinear least squares (scipy.optimize.least_squares with robust loss)
          Staged: hover parameters first, then rotational dynamics, then drag
          Constraints: physical bounds (mass > 0, inertia positive definite, etc.)
          Uncertainty: Gauss-Newton approximate Hessian for confidence intervals;
                       bootstrap resampling across log windows for robustness check

Stage 4: Sensor Parameter Estimator
  Input:  Pre-arm static IMU windows + hover IMU windows
  Output: SIM_ACC1_BIAS, SIM_GYR1_BIAS (bias vectors, m/s^2 and rad/s)
          SIM_ACC1_RND, SIM_GYR1_RND (noise proxy scalars)
          SIM_ACC1_SCAL, SIM_GYR1_SCAL (scale factors)
  Method: Static bias from pre-arm mean; noise from variance in steady hover;
          scale from ratio of estimated vs logged magnitude at known attitudes

Stage 5: Output Writers + Validation Harness
  Outputs:
    - <vehicle>_model.json: JSON frame model aligned to SIM_Frame fields
    - <vehicle>_sensor.parm: parameter file loadable by MAVProxy/sim_vehicle.py
    - fit_report.txt: parameter values, confidence intervals, identifiability
                       warnings (condition number, parameter correlations)
  Validation:
    - Replay fitted model against held-out log windows
    - Compute RMS attitude error (deg), RMS body-rate error (rad/s),
      RMS linear acceleration error (m/s^2), PSD mismatch score
    - Report improvement vs ArduPilot default model parameters
```

The pipeline intentionally mirrors ArduPilot's existing multicopter frame model structure so
that every estimated parameter maps directly to a field in the JSON that SITL can already load.
No new simulation format is introduced.

---

## Project Plan and Timeline

**Pre-application work (done)**
- SITL environment set up locally (sim_vehicle.py running, ArduPilot compiled)
- Log parser working: pymavlink DFReader_binary parsing CTUN, RCOU, BAT, PARM messages
- hoverThrOut, propExpo, PWM range, battery params extracted from real .bin log
- Code at github.com/bandaru6/gsoc-sitl-sysid
- Forum post submitted to discuss.ardupilot.org GSoC category
- Proposal draft shared with mentor for feedback

**Community Bonding (May 8 – June 1) — not counted in 350h**
- Sync with Nathaniel Mailhot on: preferred log types (SYSID vs ordinary), priority parameters,
  and where tooling should live (Tools/scripts vs external repo)
- Identify 2–3 real flight logs to use as development baselines; confirm with mentor
- Set up CI (GitHub Actions) for the repo: lint, unit tests, sample log regression test
- Read through SIM_Frame.cpp and SIM_Frame.h to confirm all JSON-loadable fields
- Milestone: dev environment documented, mentor alignment confirmed, CI running

**Phase 1: Log Parser + Time Alignment (Weeks 1–3, ~70h)**

Tasks:
- Robust DataFlash .bin parser handling old and new message formats
- Time alignment: resample all message streams to common timebase using linear interpolation
- Message selection config: YAML file specifying which messages to extract per vehicle type
- Segment detection: hover (low climb rate + stable attitude), rate steps, SYSID chirp windows
- Quality filter: flag segments with GPS outages, EKF divergence, low excitation
- Unit tests: verify alignment accuracy, segment detection on synthetic and real logs
- SYSID mode support: parse SID messages, extract chirp metadata and aligned IMU response

Milestone 1 (end of Week 3):
- Parser handles >=3 different .bin logs without error
- Time-aligned DataFrame outputs verified against raw log data manually
- Segment detector correctly labels hover windows on at least 2 real logs
- All tests passing in CI

**Phase 2: Dynamics Model + Parameter Mapping (Weeks 4–6, ~80h)**

Tasks:
- Implement the grey-box multirotor dynamics model in Python, matching ArduPilot's
  SIM_Frame physics structure (thrust from motor commands, body-frame drag, rotational
  dynamics, motor lag as first-order filter)
- Map model parameters to ArduPilot JSON frame fields (mass, moment_of_inertia,
  disc_area, mdrag_coef, hoverThrOut, propExpo, motor geometry)
- Staged optimization:
  Step 1 — hoverThrOut from median CTUN.ThO during hover segments
  Step 2 — rotational inertia from angular acceleration vs motor differential torque
  Step 3 — mdrag_coef from forward-flight attitude vs airspeed relationship
- Physical bounds and constraints for each parameter
- JSON writer: outputs model file aligned to SIM_Frame loading format

Milestone 2 (end of Week 6):
- Grey-box model reproduces ArduPilot SITL physics within 5% on synthetic data
- Optimizer converges on at least 2 real logs with physically plausible parameters
- JSON output loads successfully in SITL via sim_vehicle.py custom frame path

**Phase 3: Optimization + Uncertainty Quantification (Weeks 7–8, ~70h)**

Tasks:
- Robust loss function (Huber or trimmed least squares) to handle outlier segments
- Gauss-Newton approximate Hessian for parameter confidence intervals
- Bootstrap resampling across log windows for robustness checks
- Condition number and parameter correlation diagnostics
- Identifiability warnings: flag parameters that are unidentifiable from a given log
  (e.g., inertia cannot be reliably estimated from hover-only logs)
- Regularization: soft priors on parameters using typical ArduPilot vehicle ranges

Milestone 3 (end of Week 8):
- Confidence intervals reported for all fitted parameters
- Identifiability warnings correctly flagged on logs known to lack sufficient excitation
- Optimizer stable across 5 different test logs without manual intervention

**Phase 4: Sensor Parameter Estimation + Output Writers (Weeks 9–10, ~40h)**

Tasks:
- Pre-arm static window detection (vehicle stationary, motors off)
- Accelerometer bias from mean of static IMU windows (SIM_ACC1_BIAS)
- Gyro bias from mean of static gyro windows (SIM_GYR1_BIAS)
- Noise proxy from variance in steady hover (SIM_ACC1_RND, SIM_GYR1_RND)
- Scale factor estimation (SIM_ACC1_SCAL, SIM_GYR1_SCAL) where data supports it
- .parm file writer compatible with MAVProxy parameter load/save format
- Integration: full pipeline CLI — one command from .bin to JSON + .parm + report

Milestone 4 (end of Week 10):
- SIM_ACC1_BIAS estimated within 10% of manufacturer spec on known IMU
- Full CLI runs end-to-end on a real log, outputting JSON + .parm in <60 seconds
- Parameters load successfully into SITL without error

**Phase 5: Validation Harness + Documentation (Weeks 11–12, ~40h)**

Tasks:
- Validation runner: replay fitted model against held-out log windows
  (use withheld segments not seen during optimization)
- Metrics: RMS attitude error (deg), RMS body-rate error (rad/s),
  RMS acceleration error (m/s^2), PSD mismatch score
- Compare vs ArduPilot default model parameters as baseline
- Regression tests: automated CI checks that fitted params improve over baseline on
  the sample log (prevents regressions in optimizer changes)
- fit_report.txt: human-readable summary with parameter table, confidence intervals,
  validation metrics, identifiability warnings, and usage instructions
- Full documentation: README, runbook, example with sample log output
- SYSID mode polish: document recommended flight test procedure

Milestone 5 (end of Week 12):
- Validation shows >=30% RMS attitude error reduction vs default model on held-out
  windows, on at least 2 real logs
- CI regression tests passing
- Full documentation merged
- Runbook: developer can go from raw .bin to running SITL with fitted model in <15 min

**Timeline Summary**

| Phase | Weeks | Hours | Key Deliverable |
|-------|-------|-------|-----------------|
| Bonding | Pre-coding | — | Dev env, mentor sync, CI |
| 1: Log Parser | 1–3 | 70h | Robust parser, time alignment, segment detection |
| 2: Dynamics Model | 4–6 | 80h | Grey-box optimizer, JSON writer, SITL validation |
| 3: Uncertainty | 7–8 | 70h | Confidence intervals, identifiability diagnostics |
| 4: Sensor Params | 9–10 | 40h | IMU bias/noise, .parm writer, full CLI |
| 5: Validation + Docs | 11–12 | 40h | Metrics, regression tests, documentation |
| Buffer | — | 50h | Risk mitigation, mentor feedback, polish |
| Total | 12 weeks | 350h | End-to-end toolchain |

---

## Performance Evaluation

I will evaluate the toolchain on both accuracy and robustness using the following approach:

Primary metrics (reported in fit_report.txt for every run):

| Metric | Definition | Target |
|--------|-----------|--------|
| RMS attitude error | Quaternion angle distance, fitted SITL vs real log (deg) | >=30% reduction vs default |
| RMS body-rate error | Gyro rate residual on held-out window (rad/s) | Stable across maneuvers |
| RMS acceleration error | Body-frame accel residual (m/s^2) | Reduced across hover + forward flight |
| PSD mismatch score | Welch PSD distance between fitted sim and real acceleration | Reduced resonance mismatch |
| Parameter CI coverage | Fraction of parameters with finite confidence intervals | 100% on SYSID logs |
| Cross-log generalization | Validation error on a different log than training log | Bounded degradation |

Datasets:
- Sample logs from the ArduPilot test suite and forum (publicly available .bin files)
- SITL-generated synthetic logs (known ground truth parameters, used for optimizer unit tests)
- If mentor can provide SYSID-mode chirp logs: primary development baseline
- At minimum one custom hover+maneuver flight (can be generated in SITL with parameter noise)

For optimizer unit tests, I will generate synthetic logs by running SITL with known parameters,
injecting Gaussian noise matching typical sensor specs, then verifying that the optimizer
recovers the known parameters within the expected confidence interval.

---

## Technical Skills

Programming experience:
Python (primary — 3 years), C++ (2 years, including ongoing research work in simulation
pipelines at BLENDER Lab), R (1 year, statistical analysis). I have used numpy, scipy,
pandas, and matplotlib extensively for data analysis and optimization. I am comfortable with
the scipy.optimize family of methods — least_squares, minimize, curve_fit — and understand
their numerical properties (Jacobian computation, trust-region vs Levenberg-Marquardt,
condition number interpretation). I have worked with pymavlink previously for parsing MAVLink
telemetry streams.

For this project specifically, I have already:
- Set up the ArduPilot build environment and run SITL with sim_vehicle.py
- Written a working DataFlash .bin parser using DFReader_binary
- Read through SIM_Frame.cpp to understand the JSON-loadable parameter structure
- Implemented the starter log-to-JSON extraction script (code sample below)

---

## Code Samples

Working log parser (demonstrates ArduPilot toolchain familiarity):
github.com/bandaru6/gsoc-sitl-sysid/blob/main/Tools/scripts/log_to_model_params.py

This script parses a DataFlash .bin log, extracts hoverThrOut from CTUN.ThO (with
normalization for both old 0-1000 scale and new 0-1 formats), propExpo from
MOT_THST_EXPO, PWM range from RCOU, and battery parameters from BAT messages, and
outputs a SITL-compatible JSON frame model. It was tested on a real ArduPilot .bin log and
produces physically reasonable values (hoverThrOut: 0.387, propExpo: 0.8).

---

## Open Source Experience

I have contributed to research code pipelines at UIUC's BLENDER Lab that are shared
internally and structured for reproducibility — version-controlled, tested, and documented for
use by other lab members. While I have not yet made a merged PR to a major open source
project, I have been actively studying the ArduPilot codebase in preparation for this project:
reading sim_vehicle.py, SIM_Frame.cpp, the DataFlash log message reference, and the SYSID
mode documentation. I have set up a public GitHub repo for this project's tooling and plan to
make incremental PRs to the main ArduPilot repository starting with the log parser utilities.

Why I want to contribute to open source: ArduPilot is used by thousands of researchers and
developers who cannot afford extensive hardware testing. A tool that makes SITL more
accurately reflect real vehicles has immediate practical value — it reduces the time between
"this works in simulation" and "this works on a real drone." That is the kind of contribution I
want to make.

---

## Background and Education

- University: University of Illinois Urbana-Champaign
- Major: B.S. Computer Science + B.S. Statistics (dual degree)
- Year: Sophomore (2 years completed by summer 2026)
- GPA: 3.83/4.0
- Relevant coursework: Computational Linear Algebra, Statistical Computing, Applied ML,
  Data Structures and Algorithms, Computer Architecture, Probability Theory

Research:
I work as an undergraduate researcher at UIUC's BLENDER Lab under Prof. Shenlong Wang,
where I build simulation evaluation infrastructure for autonomous driving systems. My work
involves C++ simulation components, trajectory rollout pipelines, and counterfactual scenario
generation for causal inference. The core challenge — making simulated behavior match
real-world dynamics — is the same problem this project addresses, applied to flight dynamics
instead of autonomous driving.

---

## Research Context

The most relevant paper for this project is:

Burri et al. (2020), "Identification of the Propeller Coefficients and Dynamic Parameters of
a Hovering Quadrotor From Flight Data," IEEE Robotics and Automation Letters. This paper
establishes the standard grey-box identification approach for multicopters: fix the rigid-body
dynamics structure, estimate a small set of physically meaningful parameters (thrust
coefficient, drag, inertia) from flight data using prediction error methods. The parameter set
and estimation structure I am implementing closely follow this work.

I have also read:
- Ljung (1999), System Identification: Theory for the User — canonical reference on
  prediction error methods, maximum likelihood, and identifiability
- Mahony et al. (2012), Multirotor Aerial Vehicles: Modeling, Estimation, and Control —
  establishes the dynamics model structure (rigid body + thrust + drag) that I am fitting
- ArduPilot SYSID mode documentation — establishes the chirp injection workflow and
  explains what SID log messages contain

I have not authored a published paper, but I am actively involved in research that could lead to
a publication on simulation evaluation methodology for autonomous systems.

---

## GSoC Experience

I have not participated in a previous Google Summer of Code.

I am not applying to any other GSoC project. My full focus is on this proposal.

Why GSoC: I applied because this is one of the only programs where I can spend a summer
working on a real systems problem that matters — not a tutorial project, not a toy dataset, but
a tool that ArduPilot developers will actually use to make their simulations better. The
technical challenge (system identification from noisy flight data) is exactly the kind of
problem I want to get deeply good at.

Why ArduPilot: ArduPilot is the most widely deployed open-source autopilot in the world.
The SITL toolchain is central to how the community develops and validates new features.
Making SITL fidelity better has a direct multiplier effect on every project that uses SITL for
testing — which is essentially everyone. That reach is what makes this worth spending a
summer on.

---

## Summer Plans

- Location: Plano, TX (home), with access to UIUC resources remotely
- Availability: 30 hours/week, with capacity to push harder during key development phases
- Conflicts: No summer classes, no internship. One 3–4 day family trip in late June,
  scheduled to avoid milestone deadlines.

---

## Coding Period

I prefer the standard 12-week coding period (approximately June through August 2026).
The 350-hour scope maps cleanly to 12 weeks at 25–30 hours/week with a 50-hour buffer
for mentor feedback cycles, unexpected technical blockers, and final polish. I am not planning
any extension — the 12-week scope is realistic given the architecture I have already thought
through and the pre-work I have already completed.

---

## In Two Sentences, Why Should You Take Me?

I have already set up the development environment, read the relevant source files, written a
working parser, and posted on the forum before submitting this proposal — I am not applying
to learn what SITL is, I am applying to spend 350 hours making it better. My Statistics
background gives me a real advantage on the hardest part of this project: not writing the
optimizer, but understanding when its output can be trusted and when it cannot.
