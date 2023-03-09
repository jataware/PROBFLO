# PROBFLO
Python wrappers for Netica model simulations.

## Requirements
- NeticaPy3: https://github.com/jataware/NeticaPy3
- pandas

## Current Scenarios
- [Mara](docs/mara.md)
- [Limpopo](docs/limpopo.md)

## Local Usage
If the netica model is too large, a netica license is required. To run with a license, the `NETICA_PASSWORD` environment variable must be set to a valid license key.

Set model inputs in [configs/\<scenario>.json](configs/)
- Variables may be set to either `null`, an integer selecting the nth belief state, or the string of the belief state.
    - `null` leaves the variable with its default distribution as defined in the .neta file. For example, setting all variables to `null` runs the default configuration of the model without any interventions.
    - Selecting a specific belief state for a node will clamp that bin of the distribution to 100%, and zero for all others.
    - Most variables have a distribution with 4 belief states/bins: `'Zero'`, `'Low'`, `'Med'`, `'High'`
        - e.g. in the limpopo scenario, `"WQ_ECOSYSTEM"` can be set with any of these strings, or an integer in `[0-3]`
    - Certain continuous input variables do not have named belief states, and the desired bin must be set with an integer.
        - e.g. in the limpopo scenario, `"DISCHARGE_LF"` can be set with an integer in `[0-28]`


Run the scenario, optionally specifying the path to the Netica file
```
$ python <scenario>.py [neta/<scenario>.neta]
```
for example:
```
$ python mara.py neta/mara.neta
$ python limpopo.py
```

Results are output to [results](results/) as a CSV file.


## Docker Usage

First build the container with:

```
docker build -t probflo .
```

Then run:

```
docker run --rm -v $PWD:/project probflo python mara.py neta/mara.neta
```

Results will be written to a `results` directory.

