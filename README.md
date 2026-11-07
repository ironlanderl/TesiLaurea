# TesiLaurea
Software for Attack and Defense CTF challenges.

> [!NOTE]
> While not needed for operation, the included submodule could be useful for experimentation and as a checker implementation reference. Clone it with
> `git clone https://github.com/ironlanderl/TesiLaurea --recursive`

## Orchestrator
Handles the various checkers. Optionally can output data to prometheus to be viewed with the provided grafana dashboard.

```
usage: main.py [-h] [--ticks TICKS] [--tick-time TICK_TIME] [--teams TEAMS]
               [--prometheus] [--prometheus-port PROMETHEUS_PORT]
               [--prometheus-host PROMETHEUS_HOST] [--colored]
               [checkers ...]

positional arguments:
  checkers              Path to a checker directory. Defaults to the
                        ccitAD2024 checkers if not provided (default: None)

options:
  -h, --help            show this help message and exit
  --ticks TICKS         Number of ticks to run (default: 6)
  --tick-time TICK_TIME
                        Tick duration in seconds (default: 120)
  --teams TEAMS         Number of teams present (default: 1)
  --prometheus          Enables prometheus data exporting (default: False)
  --prometheus-port PROMETHEUS_PORT
                        Port to use for prometheus (default: 8500)
  --prometheus-host PROMETHEUS_HOST
                        Host to use for prometheus (default: 0.0.0.0)
  --colored             Enables colored console output (default: False)
```

## FlagIdService
Simple Flask service to handle storage and viewing of flagIds.
To use it, run:
- `make` to run and create a new database if missing, or resuming if an existing database is found
- `make run-new` to run after resetting the database
- `make test` to run the provided tests with pytest

All three will automatically setup a virtual environment using `uv` if not found
