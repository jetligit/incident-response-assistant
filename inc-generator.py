"""
Synthetic incident generator for the AI incident response agent project.

Generates realistic log lines + metric time series for common production
failure patterns, plus the matching "ground truth" root cause so you can
score your agent's diagnosis against something concrete.

Usage:
    python incident_generator.py --scenario memory_leak --out incident_001
    python incident_generator.py --scenario random --count 20 --out batch
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Service topology — a small fake microservice graph so logs/metrics feel like
# they come from a real system rather than one box producing everything.
# ---------------------------------------------------------------------------

SERVICES = [
    "api-gateway",
    "auth-service",
    "orders-service",
    "payments-service",
    "inventory-service",
    "notifications-worker",
]

HOSTS = {svc: [f"{svc}-{i}" for i in range(1, 4)] for svc in SERVICES}

LOG_LEVELS = ["INFO", "WARN", "ERROR", "DEBUG"]

NORMAL_LOG_TEMPLATES = [
    "Request {req_id} completed in {latency}ms",
    "Health check OK",
    "Cache hit for key user:{user_id}",
    "Processed batch of {n} items",
    "Connection established to downstream {downstream}",
    "Scheduled job '{job}' completed successfully",
]


def _ts(base: datetime, offset_seconds: float) -> str:
    return (base + timedelta(seconds=offset_seconds)).isoformat() + "Z"


def _rand_req_id() -> str:
    return uuid.uuid4().hex[:10]


# ---------------------------------------------------------------------------
# Scenario definitions
#
# Each scenario is a function(base_time, duration_s) -> (logs, metrics, truth)
#   logs:    list of dicts {timestamp, level, service, host, message}
#   metrics: dict[metric_name] -> list of {timestamp, value} (per service)
#   truth:   dict describing the actual root cause (your eval ground truth)
# ---------------------------------------------------------------------------

def scenario_memory_leak(base_time: datetime, duration_s: int = 1800):
    """Slow climb in memory usage over time until the process is OOM-killed."""
    service = "orders-service"
    host = random.choice(HOSTS[service])
    logs, mem_series, cpu_series, err_series = [], [], [], []

    step = 30  # seconds between samples
    leak_start_mem = 35.0  # percent
    for t in range(0, duration_s, step):
        # Memory climbs roughly linearly with noise, accelerating near the end
        progress = t / duration_s
        mem = leak_start_mem + progress * 55 + random.uniform(-1.5, 1.5)
        mem = min(mem, 99)
        cpu = 20 + random.uniform(-5, 5) + (10 if progress > 0.85 else 0)
        err_rate = 0.5 if progress < 0.8 else 0.5 + (progress - 0.8) * 40

        mem_series.append({"timestamp": _ts(base_time, t), "value": round(mem, 1)})
        cpu_series.append({"timestamp": _ts(base_time, t), "value": round(max(cpu, 0), 1)})
        err_series.append({"timestamp": _ts(base_time, t), "value": round(max(err_rate, 0), 2)})

        if progress > 0.85 and random.random() < 0.4:
            logs.append({
                "timestamp": _ts(base_time, t),
                "level": "WARN",
                "service": service,
                "host": host,
                "message": f"GC pause exceeded threshold ({random.randint(800, 2500)}ms)",
            })
        if progress > 0.95 and random.random() < 0.5:
            logs.append({
                "timestamp": _ts(base_time, t),
                "level": "ERROR",
                "service": service,
                "host": host,
                "message": "java.lang.OutOfMemoryError: Java heap space",
            })

    # Final OOM kill event
    kill_t = duration_s - step
    logs.append({
        "timestamp": _ts(base_time, kill_t + 5),
        "level": "ERROR",
        "service": service,
        "host": host,
        "message": f"Process killed by OOM killer (host {host}, rss=98.2%)",
    })
    logs.append({
        "timestamp": _ts(base_time, kill_t + 8),
        "level": "INFO",
        "service": service,
        "host": host,
        "message": "Container restarted by orchestrator (restartCount=1)",
    })

    truth = {
        "root_cause": "memory_leak",
        "service": service,
        "host": host,
        "summary": (
            "Steady upward memory growth over ~30 minutes with no corresponding "
            "drop on GC, culminating in an OOM kill. Classic unbounded memory leak "
            "(e.g. unclosed connections, growing in-memory cache, or accumulating "
            "event listeners)."
        ),
        "expected_signals": [
            "memory.percent trending up monotonically",
            "GC pause warnings increasing in frequency near the end",
            "OutOfMemoryError in logs immediately before restart",
        ],
        "suggested_fix": "Restart is a temporary mitigation. Needs heap dump analysis "
                          "to find the leaking object reference; check recently deployed "
                          "code for unbounded caches or unclosed resources.",
    }

    metrics = {
        "memory.percent": {service: mem_series},
        "cpu.percent": {service: cpu_series},
        "error_rate": {service: err_series},
    }
    return logs, metrics, truth


def scenario_connection_pool_exhaustion(base_time: datetime, duration_s: int = 900):
    """Sudden traffic spike exhausts the DB connection pool."""
    service = "payments-service"
    host = random.choice(HOSTS[service])
    downstream = "payments-db"
    logs, conn_series, latency_series, err_series = [], [], [], []

    step = 15
    spike_t = duration_s * 0.4  # spike happens 40% into the window
    pool_max = 50

    for t in range(0, duration_s, step):
        if t < spike_t:
            conns = random.uniform(8, 15)
            latency = random.uniform(20, 50)
            err_rate = random.uniform(0, 0.3)
        else:
            since_spike = t - spike_t
            ramp = min(since_spike / 60, 1.0)
            conns = min(pool_max, 15 + ramp * 60)
            latency = 30 + ramp * 900 + random.uniform(-20, 20)
            err_rate = ramp * 35 + random.uniform(-2, 2)

            if conns >= pool_max and random.random() < 0.6:
                logs.append({
                    "timestamp": _ts(base_time, t),
                    "level": "ERROR",
                    "service": service,
                    "host": host,
                    "message": f"Timeout waiting for connection from pool '{downstream}' "
                               f"(active={pool_max}, max={pool_max}, waited=5000ms)",
                })

        conn_series.append({"timestamp": _ts(base_time, t), "value": round(min(conns, pool_max), 1)})
        latency_series.append({"timestamp": _ts(base_time, t), "value": round(max(latency, 0), 1)})
        err_series.append({"timestamp": _ts(base_time, t), "value": round(max(err_rate, 0), 2)})

    logs.append({
        "timestamp": _ts(base_time, spike_t + 5),
        "level": "WARN",
        "service": service,
        "host": host,
        "message": f"Incoming request rate increased 6x over baseline (deploy_id unrelated)",
    })

    truth = {
        "root_cause": "connection_pool_exhaustion",
        "service": service,
        "host": host,
        "downstream": downstream,
        "summary": (
            "A sharp traffic spike drove DB connection pool usage to its configured "
            "max, causing request timeouts and a sustained spike in p99 latency and "
            "error rate. The pool size, not the database itself, is the bottleneck."
        ),
        "expected_signals": [
            "active_connections flatlining at pool max",
            "latency.p99 climbing sharply after the spike",
            "'Timeout waiting for connection from pool' errors in logs",
        ],
        "suggested_fix": "Increase pool size as a short-term mitigation; add backpressure "
                          "/ request queuing and investigate whether the traffic spike was "
                          "legitimate or a retry storm from an upstream caller.",
    }

    metrics = {
        "db.active_connections": {service: conn_series},
        "latency.p99_ms": {service: latency_series},
        "error_rate": {service: err_series},
    }
    return logs, metrics, truth


def scenario_disk_full(base_time: datetime, duration_s: int = 2400):
    """Disk usage climbs steadily (e.g. unrotated logs) until writes start failing."""
    service = "notifications-worker"
    host = random.choice(HOSTS[service])
    logs, disk_series, err_series = [], [], []

    step = 60
    for t in range(0, duration_s, step):
        progress = t / duration_s
        disk = 60 + progress * 38 + random.uniform(-1, 1)
        err_rate = 0 if progress < 0.9 else (progress - 0.9) * 80

        disk_series.append({"timestamp": _ts(base_time, t), "value": round(min(disk, 100), 1)})
        err_series.append({"timestamp": _ts(base_time, t), "value": round(max(err_rate, 0), 2)})

        if progress > 0.9 and random.random() < 0.5:
            logs.append({
                "timestamp": _ts(base_time, t),
                "level": "ERROR",
                "service": service,
                "host": host,
                "message": "OSError: [Errno 28] No space left on device: '/var/log/app/worker.log'",
            })

    logs.append({
        "timestamp": _ts(base_time, duration_s * 0.3),
        "level": "WARN",
        "service": service,
        "host": host,
        "message": "Log rotation job 'logrotate-daily' has not run in 9 days",
    })

    truth = {
        "root_cause": "disk_full",
        "service": service,
        "host": host,
        "summary": (
            "Disk usage climbed steadily over hours due to a failed log rotation "
            "job, eventually exhausting available space and causing write failures."
        ),
        "expected_signals": [
            "disk.percent trending up steadily with no drops",
            "log rotation job missing from scheduled runs",
            "'No space left on device' errors once disk nears 100%",
        ],
        "suggested_fix": "Clear old logs to recover space immediately; fix the broken "
                          "logrotate cron/job and add a disk-usage alert threshold below 90%.",
    }

    metrics = {
        "disk.percent": {service: disk_series},
        "error_rate": {service: err_series},
    }
    return logs, metrics, truth


def scenario_bad_deploy(base_time: datetime, duration_s: int = 600):
    """A new deploy introduces a bug that immediately spikes 500 errors."""
    service = "auth-service"
    host = random.choice(HOSTS[service])
    logs, err_series, latency_series = [], [], []

    step = 10
    deploy_t = 60
    for t in range(0, duration_s, step):
        if t < deploy_t:
            err_rate = random.uniform(0, 0.5)
            latency = random.uniform(40, 80)
        else:
            err_rate = random.uniform(45, 60)
            latency = random.uniform(60, 120)
            if random.random() < 0.7:
                logs.append({
                    "timestamp": _ts(base_time, t),
                    "level": "ERROR",
                    "service": service,
                    "host": host,
                    "message": "TypeError: cannot read property 'token' of undefined "
                               "at validateSession (auth/session.js:142)",
                })

        err_series.append({"timestamp": _ts(base_time, t), "value": round(err_rate, 2)})
        latency_series.append({"timestamp": _ts(base_time, t), "value": round(latency, 1)})

    logs.insert(0, {
        "timestamp": _ts(base_time, deploy_t - 2),
        "level": "INFO",
        "service": service,
        "host": host,
        "message": "Deploy completed: version=v2.14.3 commit=8a31f02",
    })

    truth = {
        "root_cause": "bad_deploy",
        "service": service,
        "host": host,
        "summary": (
            "A deploy at t=58s introduced a null-reference bug in session validation, "
            "causing an immediate and sustained spike in 500 errors with no change in "
            "traffic volume."
        ),
        "expected_signals": [
            "error_rate step-changes immediately after a deploy log line",
            "Latency relatively unaffected — this is a logic bug, not a load issue",
            "Same TypeError repeating across many requests",
        ],
        "suggested_fix": "Roll back to the previous version (commit before 8a31f02) "
                          "immediately; the deploy timestamp correlates exactly with "
                          "the error spike onset.",
    }

    metrics = {
        "error_rate": {service: err_series},
        "latency.p99_ms": {service: latency_series},
    }
    return logs, metrics, truth


SCENARIOS = {
    "memory_leak": scenario_memory_leak,
    "connection_pool_exhaustion": scenario_connection_pool_exhaustion,
    "disk_full": scenario_disk_full,
    "bad_deploy": scenario_bad_deploy,
}


# ---------------------------------------------------------------------------
# Background noise — normal logs from OTHER services running concurrently,
# so the agent has to actually find the signal instead of everything in the
# payload being relevant.
# ---------------------------------------------------------------------------

def generate_background_noise(base_time: datetime, duration_s: int, exclude_service: str):
    logs = []
    noisy_services = [s for s in SERVICES if s != exclude_service]
    step = 20
    for t in range(0, duration_s, step):
        if random.random() < 0.6:
            svc = random.choice(noisy_services)
            host = random.choice(HOSTS[svc])
            template = random.choice(NORMAL_LOG_TEMPLATES)
            message = template.format(
                req_id=_rand_req_id(),
                latency=random.randint(15, 200),
                user_id=random.randint(1000, 9999),
                n=random.randint(5, 200),
                downstream=random.choice(SERVICES),
                job=random.choice(["cleanup", "reconcile-orders", "sync-inventory"]),
            )
            logs.append({
                "timestamp": _ts(base_time, t),
                "level": "INFO",
                "service": svc,
                "host": host,
                "message": message,
            })
    return logs


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def generate_incident(scenario_name: str, seed: int | None = None):
    if seed is not None:
        random.seed(seed)

    if scenario_name == "random":
        scenario_name = random.choice(list(SCENARIOS.keys()))

    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario_name}'. Options: {list(SCENARIOS)}")

    base_time = datetime(2026, 6, 22, 9, 0, 0) - timedelta(days=random.randint(0, 14))
    fn = SCENARIOS[scenario_name]
    logs, metrics, truth = fn(base_time)

    duration_s = max(
        int((datetime.fromisoformat(l["timestamp"].replace("Z", "")) - base_time).total_seconds())
        for l in logs
    ) + 60

    noise = generate_background_noise(base_time, duration_s, exclude_service=truth["service"])
    all_logs = sorted(logs + noise, key=lambda l: l["timestamp"])

    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    truth["incident_id"] = incident_id
    truth["scenario"] = scenario_name

    payload = {
        "incident_id": incident_id,
        "alert": {
            "fired_at": all_logs[-1]["timestamp"],
            "service": truth["service"],
            "title": _alert_title_for(scenario_name, truth),
        },
        "logs": all_logs,
        "metrics": metrics,
    }
    return payload, truth


def _alert_title_for(scenario_name: str, truth: dict) -> str:
    titles = {
        "memory_leak": f"High memory usage on {truth['service']}",
        "connection_pool_exhaustion": f"Elevated latency / error rate on {truth['service']}",
        "disk_full": f"Disk usage critical on {truth['service']}",
        "bad_deploy": f"Error rate spike on {truth['service']}",
    }
    return titles[scenario_name]


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic incident data.")
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()) + ["random"],
        default="random",
        help="Which failure scenario to generate.",
    )
    parser.add_argument("--count", type=int, default=1, help="Number of incidents to generate.")
    parser.add_argument("--out", default="incident", help="Output filename prefix.")
    parser.add_argument("--outdir", default=".", help="Output directory.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    index = []
    for i in range(args.count):
        seed = (args.seed + i) if args.seed is not None else None
        payload, truth = generate_incident(args.scenario, seed=seed)

        fname = f"{args.out}_{i+1:03d}.json" if args.count > 1 else f"{args.out}.json"
        truth_fname = fname.replace(".json", ".truth.json")

        (outdir / fname).write_text(json.dumps(payload, indent=2))
        (outdir / truth_fname).write_text(json.dumps(truth, indent=2))

        index.append({"file": fname, "truth_file": truth_fname, "scenario": truth["scenario"],
                       "incident_id": truth["incident_id"]})
        print(f"Generated {fname} (scenario={truth['scenario']}, "
              f"logs={len(payload['logs'])}, incident_id={truth['incident_id']})")

    if args.count > 1:
        (outdir / f"{args.out}_index.json").write_text(json.dumps(index, indent=2))
        print(f"\nWrote index to {args.out}_index.json")


if __name__ == "__main__":
    main()