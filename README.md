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
- Variables may be set to either `'Zero'`, `'Low'`, `'Med'`, `'High'`, or `null`
- `null` leaves the variable in its default state, representing a distribution over the probability of `'Zero'`, `'Low'`, `'Med'`, and `'High'`. For example, setting all variables to `null` runs the default configuration of the model without any interventions.
- setting `'Zero'`, `'Low'`, `'Med'`, or `'High'` clamps the distribution to 100% for that field, and zero for all others

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

